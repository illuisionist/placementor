# PlaceMentor AI — Celery Task Queue

This directory contains the **Celery** background task infrastructure for
PlaceMentor AI (Phase 4 Track B).

---

## Prerequisites

| Dependency | Version | Purpose |
|---|---|---|
| Redis | ≥ 6.x | Celery broker **and** result backend |
| psycopg2-binary | ≥ 2.9.9 | Sync PostgreSQL driver for worker DB access |
| celery | ≥ 5.3.6 | Task queue |

### Start Redis (Docker)

If Redis is not already running locally:

```bash
docker run -d -p 6379:6379 --name placementor-redis redis:alpine
```

---

## Starting the Worker

Run from the **`backend/`** directory:

```bash
# Foreground worker (development)
celery -A tasks.celery_app worker --loglevel=info

# Multiple concurrency processes (production)
celery -A tasks.celery_app worker --loglevel=info --concurrency=4
```

---

## Starting Celery Beat (Scheduler)

```bash
celery -A tasks.celery_app beat --loglevel=info
```

> **Tip:** Run the worker and beat scheduler in **separate terminals** (or use
> the `--beat` flag on the worker for single-process development only):
>
> ```bash
> celery -A tasks.celery_app worker --beat --loglevel=info
> ```

---

## Periodic Schedule (Beat)

| Schedule Name | Task | When |
|---|---|---|
| `weekly-progress-report` | `send_weekly_progress_report` | Every **Monday 08:00 IST** |
| `advance-roadmap-weeks` | `advance_roadmap_weeks` | Every **Sunday 00:00 IST** |
| `cleanup-stale-sessions` | `cleanup_stale_sessions` | **Daily 02:00 IST** |
| `company-announcement-pipeline` | `process_company_announcements` | **Daily 09:00 IST** |

---

## Calling Tasks Manually

### Via CLI

```bash
# Process all active students
celery -A tasks.celery_app call tasks.workflows.send_weekly_progress_report

# Process a single student
celery -A tasks.celery_app call tasks.workflows.send_weekly_progress_report --args='["<user-uuid>"]'

# Advance all roadmap weeks
celery -A tasks.celery_app call tasks.workflows.advance_roadmap_weeks

# Clean stale Redis sessions
celery -A tasks.celery_app call tasks.workflows.cleanup_stale_sessions

# Broadcast company announcements
celery -A tasks.celery_app call tasks.workflows.process_company_announcements

# Run post-interview analysis for a specific interview
celery -A tasks.celery_app call tasks.workflows.post_interview_analysis --args='["<interview-uuid>"]'
```

### Via Python (from anywhere in the backend)

```python
from tasks.workflows import post_interview_analysis

# Fire-and-forget (async)
post_interview_analysis.delay(interview_id="<uuid>")

# Apply with ETA (run in 5 minutes)
from datetime import datetime, timedelta
post_interview_analysis.apply_async(
    args=["<uuid>"],
    eta=datetime.utcnow() + timedelta(minutes=5),
)
```

### Via FastAPI router (existing pattern)

```python
# In any router file after interview completion:
from tasks.workflows import post_interview_analysis
post_interview_analysis.delay(interview_id=str(interview.id))
```

---

## Task Reference

### `send_weekly_progress_report(user_id=None)`
- Fetches every active student (or one if `user_id` is supplied).
- Reads their latest active roadmap and calculates `completion_pct`.
- Creates a `Notification` row (`type=general`) with a progress summary.

### `advance_roadmap_weeks()`
- Increments `current_week` for every active roadmap (capped at `duration_weeks`).
- Recalculates `completion_pct = (current_week / duration_weeks) * 100`.
- Creates a `Notification` row (`type=roadmap`) for each advanced roadmap.

### `cleanup_stale_sessions()`
- Scans Redis for `session:*` keys with **no TTL** (`TTL == -1`, orphaned keys).
- Deletes them and returns a count.

### `process_company_announcements()`
- Generates mock campus-drive announcements (TCS, Infosys, Wipro).
- Fans them out as `Notification` rows (`type=placement`) for all active students.
- Swap `announcements` list with real scraper output in production.

### `post_interview_analysis(interview_id)`
- Called directly from the chat router after interview completion.
- Aggregates per-question scores from the `transcript` JSON field.
- Persists `overall_score` to the `MockInterview` row.
- Creates a detailed `Notification` row (`type=interview`) with score + tips.

---

## Monitoring

```bash
# Inspect active tasks
celery -A tasks.celery_app inspect active

# View registered tasks
celery -A tasks.celery_app inspect registered

# Flower (web UI) — optional
pip install flower
celery -A tasks.celery_app flower --port=5555
```

---

## File Structure

```
tasks/
├── __init__.py         # Package marker
├── celery_app.py       # Celery app + Beat schedule config
├── workflows.py        # Task implementations
└── README.md           # This file
```
