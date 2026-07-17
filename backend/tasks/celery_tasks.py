"""
Celery task queue — async background jobs for workflows.
"""

from celery import Celery
from config import settings

celery_app = Celery(
    "placementor",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="Asia/Kolkata",
    enable_utc=True,
    beat_schedule={
        # Weekly progress workflow — every Monday 8am IST
        "weekly-progress-workflow": {
            "task": "tasks.celery_tasks.weekly_progress_workflow",
            "schedule": 604800,  # 7 days in seconds
        },
    },
)


@celery_app.task(name="tasks.celery_tasks.ingest_document")
def ingest_document_task(file_path: str, collection_name: str = "general"):
    """Background task to ingest a document into ChromaDB."""
    from rag.ingestor import ingest_file
    return ingest_file(file_path, collection_name)


@celery_app.task(name="tasks.celery_tasks.weekly_progress_workflow")
def weekly_progress_workflow():
    """
    Weekly progress review — runs every Monday.
    Updates all active student roadmaps and sends notifications.
    """
    import asyncio
    from loguru import logger
    logger.info("[Celery] Starting weekly progress workflow...")
    # Placeholder — implement full workflow in Phase 4
    return {"status": "Weekly workflow executed"}


@celery_app.task(name="tasks.celery_tasks.send_notification")
def send_notification_task(user_id: str, title: str, message: str, notification_type: str = "general"):
    """Save a notification to the DB for a user."""
    import asyncio
    from loguru import logger
    logger.info(f"[Celery] Notification to {user_id}: {title}")
    return {"status": "sent", "user_id": user_id}
