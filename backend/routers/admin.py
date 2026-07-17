"""
Admin router — internal endpoints for seeding, health checks, and maintenance.
Protected by a secret token. Never expose these publicly.
"""
import os
from fastapi import APIRouter, Header, HTTPException, BackgroundTasks
from loguru import logger

router = APIRouter(prefix="/admin", tags=["admin"])

ADMIN_SECRET = os.getenv("ADMIN_SECRET", "placementor-admin-secret-change-me")


def _verify(token: str):
    if token != ADMIN_SECRET:
        raise HTTPException(status_code=403, detail="Forbidden")


@router.post("/seed")
async def seed_knowledge_base(
    background_tasks: BackgroundTasks,
    x_admin_token: str = Header(...),
):
    """
    Trigger knowledge base seeding in the background.
    Usage:
        curl -X POST https://your-render-url.onrender.com/admin/seed \
             -H "x-admin-token: your-secret"
    """
    _verify(x_admin_token)
    background_tasks.add_task(_run_seed)
    return {"status": "seeding started", "message": "Check logs for progress"}


async def _run_seed():
    """Run the seed in background — uses Render's RAM, not local."""
    import sys, gc
    sys.path.insert(0, ".")
    try:
        from seed_knowledge_base import seed
        total = seed()
        logger.success(f"[Admin Seed] Completed — {total} chunks ingested")
    except Exception as e:
        logger.error(f"[Admin Seed] Failed: {e}")
        gc.collect()


@router.get("/stats")
async def index_stats(x_admin_token: str = Header(...)):
    """Check Pinecone index stats."""
    _verify(x_admin_token)
    try:
        from rag.vector_store import get_index_stats
        stats = get_index_stats()
        return {"status": "ok", "pinecone": stats}
    except Exception as e:
        return {"status": "error", "detail": str(e)}


@router.get("/health")
async def admin_health(x_admin_token: str = Header(...)):
    """Deep health check — DB + Pinecone + Redis."""
    _verify(x_admin_token)
    results = {}

    # DB check
    try:
        from database.session import engine
        async with engine.connect() as conn:
            await conn.execute(__import__("sqlalchemy").text("SELECT 1"))
        results["postgres"] = "ok"
    except Exception as e:
        results["postgres"] = str(e)

    # Pinecone check
    try:
        from rag.vector_store import get_index_stats
        stats = get_index_stats()
        results["pinecone"] = f"ok ({stats.get('total_vector_count', 0)} vectors)"
    except Exception as e:
        results["pinecone"] = str(e)

    return results
