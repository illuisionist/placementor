"""
Celery application — uses Redis as broker and backend.

Start worker  : celery -A tasks.celery_app worker --loglevel=info
Start beat    : celery -A tasks.celery_app beat   --loglevel=info
"""

import os
import sys

# Ensure the backend package root is on sys.path regardless of the
# directory from which the worker is launched.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from celery import Celery
from celery.schedules import crontab

from config import settings

app = Celery(
    "placementor",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["tasks.workflows"],
)

app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Kolkata",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)

# ─── Celery Beat periodic schedule ────────────────────────────────────────────
app.conf.beat_schedule = {
    # Every Monday 08:00 IST
    "weekly-progress-report": {
        "task": "tasks.workflows.send_weekly_progress_report",
        "schedule": crontab(hour=8, minute=0, day_of_week="monday"),
    },
    # Every Sunday midnight — advance roadmap weeks
    "advance-roadmap-weeks": {
        "task": "tasks.workflows.advance_roadmap_weeks",
        "schedule": crontab(hour=0, minute=0, day_of_week="sunday"),
    },
    # Daily 02:00 IST — prune stale Redis sessions
    "cleanup-stale-sessions": {
        "task": "tasks.workflows.cleanup_stale_sessions",
        "schedule": crontab(hour=2, minute=0),
    },
    # Daily 09:00 IST — company announcement pipeline
    "company-announcement-pipeline": {
        "task": "tasks.workflows.process_company_announcements",
        "schedule": crontab(hour=9, minute=0),
    },
}

if __name__ == "__main__":
    app.start()
