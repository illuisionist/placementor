"""
Database session — async SQLAlchemy engine with Neon/asyncpg SSL support.

asyncpg does NOT accept `sslmode=require` as a query param (that's libpq syntax).
We strip it from the URL and pass `ssl=True` via connect_args instead.
"""
import ssl as ssl_lib
from urllib.parse import urlparse, urlencode, parse_qs, urlunparse

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from config import settings


def _build_asyncpg_url(url: str) -> tuple[str, dict]:
    """
    Strip libpq-style `sslmode` from the URL and return
    (clean_url, connect_args) suitable for asyncpg.
    """
    parsed = urlparse(url)
    params = parse_qs(parsed.query, keep_blank_values=True)

    # Pull out sslmode before asyncpg sees it
    sslmode = params.pop("sslmode", [None])[0]

    # Rebuild query string without sslmode
    new_query = urlencode({k: v[0] for k, v in params.items()})
    clean_url = urlunparse(parsed._replace(query=new_query))

    connect_args: dict = {}
    if sslmode in ("require", "verify-ca", "verify-full"):
        # Create an SSL context; disable hostname check for Neon serverless
        ctx = ssl_lib.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl_lib.CERT_NONE
        connect_args["ssl"] = ctx

    return clean_url, connect_args


_db_url, _connect_args = _build_asyncpg_url(settings.ASYNC_POSTGRES_URL)

engine = create_async_engine(
    _db_url,
    echo=settings.DEBUG,
    pool_pre_ping=True,
    pool_size=5,        # reduced for free-tier RAM
    max_overflow=10,
    connect_args=_connect_args,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    """FastAPI dependency — yields an async DB session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def create_tables():
    """Create all tables on startup (idempotent)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
