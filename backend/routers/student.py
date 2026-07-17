"""
Student router — CRUD for student profiles, resume history, roadmap, and notifications.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional

from database.session import get_db
from database.models import User, StudentProfile, Notification
from auth import get_current_user
from memory.long_term import long_term_memory

router = APIRouter(prefix="/students", tags=["Students"])


# ─── Schemas ─────────────────────────────────────────────────────────────────

class ProfileUpdateRequest(BaseModel):
    branch: Optional[str] = None
    semester: Optional[int] = None
    cgpa: Optional[float] = None
    graduation_year: Optional[int] = None
    skills: Optional[list[str]] = None
    certifications: Optional[list[str]] = None
    projects: Optional[list[dict]] = None
    internships: Optional[list[dict]] = None
    preferred_companies: Optional[list[str]] = None
    preferred_domains: Optional[list[str]] = None
    leetcode_handle: Optional[str] = None
    github_handle: Optional[str] = None
    linkedin_url: Optional[str] = None
    target_ctc_lpa: Optional[float] = None


# ─── Endpoints ───────────────────────────────────────────────────────────────

@router.get("/me")
async def get_my_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the current student's full profile."""
    profile = await long_term_memory.get_profile(db, str(current_user.id))
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return {
        "user": {
            "id": current_user.id,
            "email": current_user.email,
            "full_name": current_user.full_name,
            "role": current_user.role,
        },
        "profile": {
            "branch": profile.branch,
            "semester": profile.semester,
            "cgpa": profile.cgpa,
            "graduation_year": profile.graduation_year,
            "skills": profile.skills,
            "certifications": profile.certifications,
            "projects": profile.projects,
            "internships": profile.internships,
            "preferred_companies": profile.preferred_companies,
            "preferred_domains": profile.preferred_domains,
            "leetcode_handle": profile.leetcode_handle,
            "github_handle": profile.github_handle,
            "linkedin_url": profile.linkedin_url,
            "is_placed": profile.is_placed,
            "placed_company": profile.placed_company,
        },
    }


@router.patch("/me/profile")
async def update_my_profile(
    payload: ProfileUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update the current student's profile."""
    update_data = {k: v for k, v in payload.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields provided to update")

    profile = await long_term_memory.update_profile(db, str(current_user.id), **update_data)
    return {"message": "Profile updated successfully", "updated_fields": list(update_data.keys())}


@router.get("/me/context")
async def get_student_context(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get compact student context (used internally by agents)."""
    context = await long_term_memory.get_student_context(db, str(current_user.id))
    return context


@router.get("/me/roadmap")
async def get_active_roadmap(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the student's current active roadmap."""
    roadmap = await long_term_memory.get_active_roadmap(db, str(current_user.id))
    if not roadmap:
        return {"message": "No active roadmap found. Ask PlaceMentor to generate one!"}
    return {
        "id": roadmap.id,
        "title": roadmap.title,
        "target_company": roadmap.target_company,
        "duration_weeks": roadmap.duration_weeks,
        "current_week": roadmap.current_week,
        "completion_pct": roadmap.completion_pct,
        "weeks_plan": roadmap.weeks_plan,
    }


@router.get("/me/interviews")
async def get_interview_history(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get mock interview history."""
    interviews = await long_term_memory.get_interview_history(db, str(current_user.id))
    avg_score = await long_term_memory.get_average_interview_score(db, str(current_user.id))
    return {
        "average_score": avg_score,
        "total_interviews": len(interviews),
        "interviews": [
            {
                "id": i.id,
                "type": i.interview_type,
                "company": i.target_company,
                "score": i.overall_score,
                "status": i.status,
                "created_at": i.created_at,
            }
            for i in interviews
        ],
    }


@router.get("/me/notifications")
async def get_notifications(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all notifications for the student."""
    result = await db.execute(
        select(Notification)
        .where(Notification.user_id == str(current_user.id))
        .order_by(Notification.created_at.desc())
        .limit(20)
    )
    notifications = result.scalars().all()
    return [
        {
            "id": n.id,
            "title": n.title,
            "message": n.message,
            "type": n.notification_type,
            "is_read": n.is_read,
            "created_at": n.created_at,
        }
        for n in notifications
    ]
