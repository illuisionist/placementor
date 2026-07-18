"""
Long-term memory helpers — async wrappers over SQLAlchemy ORM.

This module provides the Memory interface that agents use to
read/write persistent student data without dealing with raw ORM.
"""

from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from database.models import StudentProfile, Resume, Roadmap, MockInterview, SkillGap, LearningHistory


class LongTermMemory:
    """Async long-term memory backed by PostgreSQL."""

    # ── Student Profile ───────────────────────────────────────────────────────

    async def get_profile(self, db: AsyncSession, user_id: str) -> Optional[StudentProfile]:
        result = await db.execute(
            select(StudentProfile).where(StudentProfile.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def update_profile(self, db: AsyncSession, user_id: str, **fields) -> StudentProfile:
        """Update specific fields on the student profile."""
        await db.execute(
            update(StudentProfile)
            .where(StudentProfile.user_id == user_id)
            .values(**fields)
        )
        await db.flush()
        return await self.get_profile(db, user_id)

    async def upsert_skill(self, db: AsyncSession, user_id: str, skill: str) -> None:
        """Add a skill to the student's skill list if not already present."""
        profile = await self.get_profile(db, user_id)
        if profile and skill not in (profile.skills or []):
            skills = list(profile.skills or [])
            skills.append(skill)
            await self.update_profile(db, user_id, skills=skills)

    # ── Resume History ────────────────────────────────────────────────────────

    async def get_active_resume(self, db: AsyncSession, user_id: str) -> Optional[Resume]:
        result = await db.execute(
            select(Resume)
            .where(Resume.user_id == user_id, Resume.is_active == True)
            .order_by(Resume.version.desc())
        )
        return result.scalar_one_or_none()

    async def get_all_resumes(self, db: AsyncSession, user_id: str) -> list[Resume]:
        result = await db.execute(
            select(Resume)
            .where(Resume.user_id == user_id)
            .order_by(Resume.version.desc())
        )
        return result.scalars().all()

    # ── Roadmap ───────────────────────────────────────────────────────────────

    async def get_active_roadmap(self, db: AsyncSession, user_id: str) -> Optional[Roadmap]:
        result = await db.execute(
            select(Roadmap)
            .where(Roadmap.user_id == user_id, Roadmap.is_active == True)
            .order_by(Roadmap.created_at.desc())
        )
        return result.scalar_one_or_none()

    async def update_roadmap_progress(
        self, db: AsyncSession, roadmap_id: str, current_week: int, completion_pct: float
    ) -> None:
        await db.execute(
            update(Roadmap)
            .where(Roadmap.id == roadmap_id)
            .values(current_week=current_week, completion_pct=completion_pct)
        )
        await db.flush()

    # ── Mock Interviews ───────────────────────────────────────────────────────

    async def get_interview_history(
        self, db: AsyncSession, user_id: str, limit: int = 10
    ) -> list[MockInterview]:
        result = await db.execute(
            select(MockInterview)
            .where(MockInterview.user_id == user_id)
            .order_by(MockInterview.created_at.desc())
            .limit(limit)
        )
        return result.scalars().all()

    async def get_average_interview_score(self, db: AsyncSession, user_id: str) -> Optional[float]:
        interviews = await self.get_interview_history(db, user_id)
        scores = [i.overall_score for i in interviews if i.overall_score is not None]
        return sum(scores) / len(scores) if scores else None

    # ── Skill Gaps ────────────────────────────────────────────────────────────

    async def get_latest_skill_gap(
        self, db: AsyncSession, user_id: str, target_company: Optional[str] = None
    ) -> Optional[SkillGap]:
        query = select(SkillGap).where(SkillGap.user_id == user_id)
        if target_company:
            query = query.where(SkillGap.target_company == target_company)
        query = query.order_by(SkillGap.created_at.desc())
        result = await db.execute(query)
        return result.scalar_one_or_none()

    # ── Learning History ──────────────────────────────────────────────────────

    async def get_completed_resources(
        self, db: AsyncSession, user_id: str
    ) -> list[LearningHistory]:
        result = await db.execute(
            select(LearningHistory)
            .where(LearningHistory.user_id == user_id, LearningHistory.completed == True)
            .order_by(LearningHistory.completed_at.desc())
        )
        return result.scalars().all()

    async def mark_resource_completed(
        self, db: AsyncSession, resource_id: str
    ) -> None:
        from datetime import datetime
        await db.execute(
            update(LearningHistory)
            .where(LearningHistory.id == resource_id)
            .values(completed=True, completed_at=datetime.utcnow())
        )
        await db.flush()

    # ── Summary for Agent Context ─────────────────────────────────────────────

    async def get_student_context(self, db: AsyncSession, user_id: str) -> dict:
        """
        Return a compact dict summary of the student's current state.
        Used by agents as input context.
        """
        profile = await self.get_profile(db, user_id)
        roadmap = await self.get_active_roadmap(db, user_id)
        avg_score = await self.get_average_interview_score(db, user_id)
        skill_gap = await self.get_latest_skill_gap(db, user_id)
        resume = await self.get_active_resume(db, user_id)

        return {
            "profile": {
                "branch": profile.branch if profile else None,
                "semester": profile.semester if profile else None,
                "cgpa": profile.cgpa if profile else None,
                "skills": profile.skills if profile else [],
                "preferred_domains": profile.preferred_domains if profile else [],
                "preferred_companies": profile.preferred_companies if profile else [],
                "certifications": profile.certifications if profile else [],
            },
            "roadmap": {
                "title": roadmap.title if roadmap else None,
                "current_week": roadmap.current_week if roadmap else None,
                "completion_pct": roadmap.completion_pct if roadmap else 0.0,
            },
            "interview": {
                "average_score": avg_score,
            },
            "skill_gaps": {
                "missing_skills": skill_gap.missing_skills if skill_gap else [],
                "weak_subjects": skill_gap.weak_subjects if skill_gap else [],
            },
            "resume": {
                "has_resume": resume is not None,
                "ats_score": resume.ats_score if resume else None,
                "strengths": resume.strengths if resume else [],
                "weaknesses": resume.weaknesses if resume else [],
                "extracted_text_preview": (resume.extracted_text[:2000] if resume and resume.extracted_text else None),
            },
        }


# Singleton instance
long_term_memory = LongTermMemory()
