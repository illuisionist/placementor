from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    # ── App ──────────────────────────────────────────────────────────────
    APP_NAME: str = "PlaceMentor AI"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    SECRET_KEY: str = "changeme-supersecret-key-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # ── Database ─────────────────────────────────────────────────────────
    POSTGRES_URL: str = "postgresql://placementor:placementor_secret@localhost:5432/placementor_db"
    ASYNC_POSTGRES_URL: str = ""

    def model_post_init(self, __context):
        if not self.ASYNC_POSTGRES_URL:
            # Auto-derive async URL from sync URL
            object.__setattr__(
                self,
                "ASYNC_POSTGRES_URL",
                self.POSTGRES_URL.replace("postgresql://", "postgresql+asyncpg://"),
            )

    # ── Redis ─────────────────────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379"
    REDIS_SESSION_TTL: int = 60 * 60 * 2  # 2 hours

    # ── Pinecone (replaces ChromaDB) ─────────────────────────────────────────
    PINECONE_API_KEY:  str = ""
    PINECONE_INDEX:    str = "placementor"
    PINECONE_ENV:      str = "us-east-1"   # Serverless region

    # ── LLM ───────────────────────────────────────────────────────────────
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    GROQ_FAST_MODEL: str = "llama-3.1-8b-instant"      # For lightweight tasks

    GOOGLE_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.0-flash"             # For document analysis

    OPENAI_API_KEY: Optional[str] = None              # Optional fallback

    # ── Embeddings ────────────────────────────────────────────────────────
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"        # Local sentence-transformers

    # ── LangSmith (optional tracing) ──────────────────────────────────────
    LANGCHAIN_TRACING_V2: bool = False
    LANGCHAIN_API_KEY: Optional[str] = None
    LANGCHAIN_PROJECT: str = "placementor-ai"

    # ── File Storage ──────────────────────────────────────────────────────
    UPLOAD_DIR: str = "uploads"
    KNOWLEDGE_BASE_DIR: str = "knowledge_base"
    MAX_UPLOAD_SIZE_MB: int = 10

    # ── RAG ───────────────────────────────────────────────────────────────
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    RETRIEVAL_TOP_K: int = 5

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
