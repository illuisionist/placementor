"""
Celery task workflows for PlaceMentor AI.

All DB operations use **synchronous** SQLAlchemy (psycopg2) because Celery
workers run in a standard (non-async) process pool.

Tasks
------
1. send_weekly_progress_report  – weekly digest for students
2. advance_roadmap_weeks        – auto-advance roadmap week pointer
3. cleanup_stale_sessions       – purge expired Redis session keys
4. process_company_announcements – mock campus-drive notification pipeline
5. post_interview_analysis      – post-mock-interview scoring & feedback
"""

import os
import sys
import uuid
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from loguru import logger
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from config import settings
from tasks.celery_app import app

# ─── Sync DB setup (psycopg2) ─────────────────────────────────────────────────

def _get_sync_db_url() -> str:
    """Convert the async (asyncpg) URL to a sync (psycopg2) URL."""
    url = settings.POSTGRES_URL  # Already a plain postgresql:// URL
    # Guard: if someone accidentally passes the asyncpg variant
    url = url.replace("postgresql+asyncpg://", "postgresql://")
    return url


_engine = create_engine(
    _get_sync_db_url(),
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
)
_SessionLocal = sessionmaker(bind=_engine, autocommit=False, autoflush=False)


def _get_session():
    """Context-manager-free session factory (caller must close)."""
    return _SessionLocal()


# ─── Lazy model imports (avoids circular import at module load time) ───────────

def _models():
    from database.models import User, StudentProfile, Roadmap, Notification, MockInterview
    return User, StudentProfile, Roadmap, Notification, MockInterview


# ─── 1. Weekly Progress Report ────────────────────────────────────────────────

@app.task(name="tasks.workflows.send_weekly_progress_report", bind=True, max_retries=3)
def send_weekly_progress_report(self, user_id: str = None):
    """
    Generate a weekly progress summary and create Notification records.

    Args:
        user_id: If supplied, process only that student; otherwise all active
                 students are processed.

    Returns:
        dict with processed count and any skipped user IDs.
    """
    User, StudentProfile, Roadmap, Notification, _ = _models()
    db = _get_session()
    processed = 0
    skipped = []

    try:
        # Build user query
        query = db.query(User).filter(User.is_active == True, User.role == "student")
        if user_id:
            query = query.filter(User.id == user_id)

        students = query.all()
        logger.info(f"[weekly_progress] Processing {len(students)} student(s).")

        for student in students:
            try:
                # Fetch the most-recently-created active roadmap
                roadmap = (
                    db.query(Roadmap)
                    .filter(Roadmap.user_id == student.id, Roadmap.is_active == True)
                    .order_by(Roadmap.created_at.desc())
                    .first()
                )

                if roadmap:
                    completion = round(roadmap.completion_pct, 1)
                    weeks_done = roadmap.current_week - 1
                    weeks_left = max(roadmap.duration_weeks - roadmap.current_week, 0)
                    summary = (
                        f"You are on Week {roadmap.current_week}/{roadmap.duration_weeks} "
                        f"of your '{roadmap.title}' roadmap. "
                        f"Overall completion: {completion}%. "
                        f"Keep going — {weeks_left} week(s) remaining!"
                    )
                else:
                    summary = (
                        "You don't have an active roadmap yet. "
                        "Head over to the Roadmap section to generate one!"
                    )

                notification = Notification(
                    id=str(uuid.uuid4()),
                    user_id=student.id,
                    title="📊 Weekly Progress Report",
                    message=summary,
                    notification_type="general",
                    is_read=False,
                )
                db.add(notification)
                processed += 1

            except Exception as exc:
                logger.warning(
                    f"[weekly_progress] Skipped user {student.id}: {exc}"
                )
                skipped.append(student.id)

        db.commit()
        logger.success(
            f"[weekly_progress] Done — {processed} notified, {len(skipped)} skipped."
        )
        return {"processed": processed, "skipped": skipped}

    except Exception as exc:
        db.rollback()
        logger.error(f"[weekly_progress] Fatal error: {exc}")
        raise self.retry(exc=exc, countdown=60)
    finally:
        db.close()


# ─── 2. Advance Roadmap Weeks ─────────────────────────────────────────────────

@app.task(name="tasks.workflows.advance_roadmap_weeks", bind=True, max_retries=3)
def advance_roadmap_weeks(self):
    """
    Auto-advance the current_week counter for every active roadmap.

    - Increments current_week by 1 (capped at duration_weeks).
    - Recalculates completion_pct.
    - Creates a 'roadmap' notification for the student.

    Returns:
        dict with advanced count.
    """
    User, StudentProfile, Roadmap, Notification, _ = _models()
    db = _get_session()
    advanced = 0

    try:
        active_roadmaps = (
            db.query(Roadmap).filter(Roadmap.is_active == True).all()
        )
        logger.info(f"[advance_roadmap] Found {len(active_roadmaps)} active roadmap(s).")

        for roadmap in active_roadmaps:
            try:
                if roadmap.current_week >= roadmap.duration_weeks:
                    # Already at final week — mark completed but don't advance
                    roadmap.completion_pct = 100.0
                    db.add(roadmap)
                    continue

                roadmap.current_week += 1
                roadmap.completion_pct = round(
                    (roadmap.current_week / roadmap.duration_weeks) * 100, 1
                )
                db.add(roadmap)

                notification = Notification(
                    id=str(uuid.uuid4()),
                    user_id=roadmap.user_id,
                    title="🗺️ Roadmap Advanced",
                    message=(
                        f"Your roadmap '{roadmap.title}' has advanced to "
                        f"Week {roadmap.current_week} of {roadmap.duration_weeks}! "
                        f"Completion: {roadmap.completion_pct}%"
                    ),
                    notification_type="roadmap",
                    is_read=False,
                )
                db.add(notification)
                advanced += 1

            except Exception as exc:
                logger.warning(
                    f"[advance_roadmap] Skipped roadmap {roadmap.id}: {exc}"
                )

        db.commit()
        logger.success(f"[advance_roadmap] Advanced {advanced} roadmap(s).")
        return {"advanced": advanced}

    except Exception as exc:
        db.rollback()
        logger.error(f"[advance_roadmap] Fatal error: {exc}")
        raise self.retry(exc=exc, countdown=60)
    finally:
        db.close()


# ─── 3. Cleanup Stale Sessions ────────────────────────────────────────────────

@app.task(name="tasks.workflows.cleanup_stale_sessions", bind=True, max_retries=3)
def cleanup_stale_sessions(self):
    """
    Scan Redis for session:* keys and delete those with TTL == -1
    (no expiry set, considered stale) or TTL < 0 (already expired / missing).

    Keys that were created more than 24 hours ago but still have a TTL set by
    the session manager are left untouched; only orphaned/never-expiring keys
    are pruned.

    Returns:
        dict with count of deleted keys.
    """
    import redis as redis_lib

    deleted = 0
    try:
        r = redis_lib.from_url(settings.REDIS_URL, decode_responses=True)
        cursor = 0
        pattern = "session:*"

        while True:
            cursor, keys = r.scan(cursor=cursor, match=pattern, count=200)
            for key in keys:
                ttl = r.ttl(key)
                # ttl == -1  → key exists but has no expiry (orphaned)
                # ttl == -2  → key does not exist (race condition)
                # ttl  > 0   → key has an active TTL — respect it
                if ttl == -1:
                    r.delete(key)
                    deleted += 1
                    logger.debug(f"[cleanup_sessions] Deleted orphaned key: {key}")

            if cursor == 0:
                break

        logger.success(f"[cleanup_sessions] Removed {deleted} stale session key(s).")
        return {"deleted": deleted}

    except Exception as exc:
        logger.error(f"[cleanup_sessions] Error: {exc}")
        raise self.retry(exc=exc, countdown=30)


# ─── 4. Company Announcement Pipeline ────────────────────────────────────────

@app.task(name="tasks.workflows.process_company_announcements", bind=True, max_retries=3)
def process_company_announcements(self):
    """
    Simulated campus-drive announcement pipeline.

    In production, this would scrape official placement portals. For now it
    generates realistic mock announcements and fans them out as Notification
    records to all active students.

    Returns:
        dict with announcement count and total notifications created.
    """
    User, StudentProfile, Roadmap, Notification, _ = _models()
    db = _get_session()

    today = datetime.now(timezone.utc).strftime("%d %b %Y")
    next_week = (datetime.now(timezone.utc) + timedelta(days=7)).strftime("%d %b %Y")

    # Mock announcements — replace with scraper in production
    announcements = [
        {
            "title": "🏢 TCS Campus Drive",
            "message": (
                f"TCS is visiting LPU on {next_week} for the System Engineer role. "
                "Eligibility: B.Tech CSE/ECE with CGPA ≥ 6.0. "
                "Register on the CDC portal by EOD."
            ),
        },
        {
            "title": "📢 Infosys Campus Drive Scheduled",
            "message": (
                f"Infosys campus drive is scheduled for {next_week}. "
                "Roles: Systems Engineer & Digital Specialist Engineer. "
                "CTC: ₹3.6 LPA – ₹6.0 LPA. Apply via the placement cell."
            ),
        },
        {
            "title": "💼 Wipro National Talent Hunt",
                "message": (
                f"Wipro NTH registration is open until {next_week}. "
                "Eligible branches: CSE, IT, ECE, EEE. Min CGPA: 6.5. "
                "Online test + HR interview. Register at careers.wipro.com."
            ),
        },
    ]

    notifications_created = 0

    try:
        students = (
            db.query(User)
            .filter(User.is_active == True, User.role == "student")
            .all()
        )
        logger.info(
            f"[announcements] Broadcasting {len(announcements)} announcement(s) "
            f"to {len(students)} student(s)."
        )

        for student in students:
            for ann in announcements:
                notif = Notification(
                    id=str(uuid.uuid4()),
                    user_id=student.id,
                    title=ann["title"],
                    message=ann["message"],
                    notification_type="placement",
                    is_read=False,
                )
                db.add(notif)
                notifications_created += 1

        db.commit()
        logger.success(
            f"[announcements] Created {notifications_created} notification(s) "
            f"({len(announcements)} announcement(s) × {len(students)} student(s))."
        )
        return {
            "announcements": len(announcements),
            "notifications_created": notifications_created,
        }

    except Exception as exc:
        db.rollback()
        logger.error(f"[announcements] Fatal error: {exc}")
        raise self.retry(exc=exc, countdown=60)
    finally:
        db.close()


# ─── 5. Post-Interview Analysis ───────────────────────────────────────────────

@app.task(name="tasks.workflows.post_interview_analysis", bind=True, max_retries=3)
def post_interview_analysis(self, interview_id: str):
    """
    Called by the chat router after a mock interview session completes.

    Steps
    -----
    1. Fetch MockInterview by id.
    2. Calculate aggregate score from transcript items.
    3. Derive improvement tips from low-scoring areas.
    4. Persist overall_score back to the interview record.
    5. Create a Notification with the score summary.

    Args:
        interview_id: UUID of the MockInterview row.

    Returns:
        dict with overall_score and notification_id.
    """
    User, StudentProfile, Roadmap, Notification, MockInterview = _models()
    db = _get_session()

    try:
        interview = db.query(MockInterview).filter(MockInterview.id == interview_id).first()

        if not interview:
            logger.warning(f"[post_interview] Interview {interview_id} not found.")
            return {"error": "Interview not found", "interview_id": interview_id}

        transcript = interview.transcript or []

        # ── Score aggregation ──────────────────────────────────────────────────
        # Transcript items are expected to be dicts with optional 'score' key (0–10)
        scores = []
        for item in transcript:
            if isinstance(item, dict):
                score = item.get("score") or item.get("rating")
                if score is not None:
                    try:
                        scores.append(float(score))
                    except (TypeError, ValueError):
                        pass

        if scores:
            overall = round(sum(scores) / len(scores), 2)
        elif interview.overall_score is not None:
            overall = interview.overall_score
        else:
            overall = 0.0

        # ── Persist score ──────────────────────────────────────────────────────
        interview.overall_score = overall
        if interview.status != "completed":
            interview.status = "completed"
            interview.completed_at = datetime.now(timezone.utc)
        db.add(interview)

        # ── Build improvement tips ─────────────────────────────────────────────
        tips = interview.improvement_suggestions or []
        if not tips:
            if overall < 4.0:
                tips = [
                    "Focus on core DSA fundamentals (arrays, trees, graphs).",
                    "Practice STAR-format answers for behavioral questions.",
                    "Work through 2–3 mock interviews each week.",
                ]
            elif overall < 7.0:
                tips = [
                    "Sharpen system design concepts (LLD & HLD).",
                    "Revise OS, DBMS, and networking fundamentals.",
                    "Improve answer conciseness — aim for 2–3 minute responses.",
                ]
            else:
                tips = [
                    "Excellent performance! Attempt company-specific problem sets.",
                    "Polish communication for senior-level technical rounds.",
                    "Start contributing to open-source to strengthen your profile.",
                ]

        tips_text = " | ".join(tips)
        interview_type_label = (interview.interview_type or "Technical").title()

        message = (
            f"Your {interview_type_label} mock interview is complete. "
            f"Overall Score: {overall}/10. "
            f"Answered {interview.total_questions} question(s). "
            f"Tips: {tips_text}"
        )

        # ── Create notification ────────────────────────────────────────────────
        notif_id = str(uuid.uuid4())
        notification = Notification(
            id=notif_id,
            user_id=interview.user_id,
            title=f"🎯 Interview Complete — Score: {overall}/10",
            message=message,
            notification_type="interview",
            is_read=False,
        )
        db.add(notification)
        db.commit()

        logger.success(
            f"[post_interview] Interview {interview_id} analysed. "
            f"Score={overall}, notification={notif_id}."
        )
        return {
            "interview_id": interview_id,
            "overall_score": overall,
            "notification_id": notif_id,
            "improvement_tips": tips,
        }

    except Exception as exc:
        db.rollback()
        logger.error(f"[post_interview] Error processing interview {interview_id}: {exc}")
        raise self.retry(exc=exc, countdown=30)
    finally:
        db.close()
