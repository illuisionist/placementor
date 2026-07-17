"""
PlaceMentor AI — FastAPI Application Entry Point

Run with:
    uvicorn main:app --reload --port 8000

API docs available at: http://localhost:8000/docs
"""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from loguru import logger

from config import settings
from database.session import create_tables
from memory.short_term import short_term_memory

# ─── Routers ──────────────────────────────────────────────────────────────────
from routers.auth import router as auth_router
from routers.student import router as student_router
from routers.chat import router as chat_router
from routers.resume import router as resume_router
from routers.admin import router as admin_router


# ─── Lifespan (startup / shutdown) ───────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 PlaceMentor AI starting up...")

    # Create DB tables
    await create_tables()
    logger.info("✅ Database tables ready")

    # Create upload directory
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    logger.info(f"✅ Upload dir ready: {settings.UPLOAD_DIR}")

    # Optionally enable LangSmith tracing
    if settings.LANGCHAIN_TRACING_V2 and settings.LANGCHAIN_API_KEY:
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_API_KEY"] = settings.LANGCHAIN_API_KEY
        os.environ["LANGCHAIN_PROJECT"] = settings.LANGCHAIN_PROJECT
        logger.info("✅ LangSmith tracing enabled")

    logger.info("✅ PlaceMentor AI is ready!")
    yield

    # Shutdown
    await short_term_memory.close()
    logger.info("👋 PlaceMentor AI shutting down...")


# ─── App ─────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="PlaceMentor AI",
    description="Intelligent placement mentorship system for LPU students",
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ─── CORS ─────────────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://localhost:8000",
    ],
    allow_origin_regex=r"https://.*\.vercel\.app|https://.*\.onrender\.com",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Routes ───────────────────────────────────────────────────────────────────

app.include_router(auth_router,    prefix="/api/v1")
app.include_router(student_router, prefix="/api/v1")
app.include_router(chat_router,    prefix="/api/v1")
app.include_router(resume_router,  prefix="/api/v1")
app.include_router(admin_router)   # no /api/v1 prefix — internal only


# ─── Health Check ────────────────────────────────────────────────────────────

@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }


@app.get("/", tags=["Root"])
async def root():
    return {
        "message": "Welcome to PlaceMentor AI 🎓",
        "docs": "/docs",
        "version": settings.APP_VERSION,
    }
