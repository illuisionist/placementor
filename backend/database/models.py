"""
SQLAlchemy ORM models for PlaceMentor AI.

Tables:
  - users            : Student & admin accounts
  - student_profiles : Extended placement profile per student
  - resumes          : Resume upload history
  - roadmaps         : Generated learning roadmaps
  - mock_interviews  : Interview sessions & scores
  - learning_history : Completed resources / videos / articles
  - notifications    : Sent notifications log
  - skill_gaps       : Persisted skill gap snapshots
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean, Column, DateTime, Enum, Float, ForeignKey,
    Integer, JSON, String, Text, func
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from database.session import Base


# ─── Helpers ─────────────────────────────────────────────────────────────────

def gen_uuid():
    return str(uuid.uuid4())


# ─── Users ────────────────────────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id            = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    email         = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name     = Column(String(255), nullable=False)
    role          = Column(Enum("student", "coordinator", "admin", name="user_role"),
                           default="student", nullable=False)
    is_active     = Column(Boolean, default=True)
    created_at    = Column(DateTime(timezone=True), server_default=func.now())
    updated_at    = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    profile       = relationship("StudentProfile", back_populates="user",
                                 uselist=False, cascade="all, delete-orphan")
    resumes       = relationship("Resume", back_populates="user",
                                 cascade="all, delete-orphan")
    roadmaps      = relationship("Roadmap", back_populates="user",
                                 cascade="all, delete-orphan")
    mock_interviews = relationship("MockInterview", back_populates="user",
                                   cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="user",
                                 cascade="all, delete-orphan")


# ─── Student Profile ──────────────────────────────────────────────────────────

class StudentProfile(Base):
    __tablename__ = "student_profiles"

    id              = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    user_id         = Column(UUID(as_uuid=False), ForeignKey("users.id"), unique=True)

    # Academic
    reg_number      = Column(String(50), unique=True, nullable=True)
    branch          = Column(String(100), nullable=True)  # e.g. "CSE", "ECE"
    semester        = Column(Integer, nullable=True)
    cgpa            = Column(Float, nullable=True)
    graduation_year = Column(Integer, nullable=True)

    # Skills & Experience
    skills          = Column(JSON, default=list)          # ["Python", "DSA", ...]
    certifications  = Column(JSON, default=list)
    projects        = Column(JSON, default=list)          # [{title, desc, tech, link}]
    internships     = Column(JSON, default=list)
    achievements    = Column(JSON, default=list)

    # Placement Preferences
    preferred_companies  = Column(JSON, default=list)
    preferred_domains    = Column(JSON, default=list)    # ["SDE", "DS", "DevOps"]
    target_ctc_lpa       = Column(Float, nullable=True)

    # Coding Profiles
    leetcode_handle      = Column(String(100), nullable=True)
    leetcode_rating      = Column(Integer, nullable=True)
    codeforces_handle    = Column(String(100), nullable=True)
    codechef_handle      = Column(String(100), nullable=True)
    github_handle        = Column(String(100), nullable=True)
    linkedin_url         = Column(String(255), nullable=True)

    # Placement Status
    is_placed       = Column(Boolean, default=False)
    placed_company  = Column(String(255), nullable=True)
    placed_ctc_lpa  = Column(Float, nullable=True)

    # Meta
    last_profile_update = Column(DateTime(timezone=True), onupdate=func.now())
    created_at      = Column(DateTime(timezone=True), server_default=func.now())

    user            = relationship("User", back_populates="profile")


# ─── Resume ───────────────────────────────────────────────────────────────────

class Resume(Base):
    __tablename__ = "resumes"

    id              = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    user_id         = Column(UUID(as_uuid=False), ForeignKey("users.id"))
    file_path       = Column(String(500), nullable=False)
    original_name   = Column(String(255), nullable=False)
    version         = Column(Integer, default=1)
    is_active       = Column(Boolean, default=True)

    # Review Results (stored as JSON from Resume Review Agent)
    ats_score       = Column(Float, nullable=True)
    strengths       = Column(JSON, default=list)
    weaknesses      = Column(JSON, default=list)
    suggestions     = Column(JSON, default=list)
    raw_review      = Column(Text, nullable=True)
    extracted_text  = Column(Text, nullable=True)

    uploaded_at     = Column(DateTime(timezone=True), server_default=func.now())

    user            = relationship("User", back_populates="resumes")


# ─── Roadmap ──────────────────────────────────────────────────────────────────

class Roadmap(Base):
    __tablename__ = "roadmaps"

    id              = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    user_id         = Column(UUID(as_uuid=False), ForeignKey("users.id"))
    title           = Column(String(255), nullable=False)
    target_company  = Column(String(255), nullable=True)
    target_role     = Column(String(255), nullable=True)
    duration_weeks  = Column(Integer, default=8)
    is_active       = Column(Boolean, default=True)

    # Roadmap content: list of weekly plans
    weeks_plan      = Column(JSON, default=list)

    # Progress tracking
    current_week    = Column(Integer, default=1)
    completion_pct  = Column(Float, default=0.0)

    created_at      = Column(DateTime(timezone=True), server_default=func.now())
    updated_at      = Column(DateTime(timezone=True), onupdate=func.now())

    user            = relationship("User", back_populates="roadmaps")


# ─── Mock Interview ───────────────────────────────────────────────────────────

class MockInterview(Base):
    __tablename__ = "mock_interviews"

    id              = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    user_id         = Column(UUID(as_uuid=False), ForeignKey("users.id"))
    interview_type  = Column(
        Enum("hr", "technical", "dsa", "core_cs", "behavioral", name="interview_type"),
        default="technical"
    )
    target_company  = Column(String(255), nullable=True)
    status          = Column(
        Enum("scheduled", "in_progress", "completed", name="interview_status"),
        default="scheduled"
    )

    # Q&A transcript stored as list of {question, answer, feedback}
    transcript      = Column(JSON, default=list)
    total_questions = Column(Integer, default=0)

    # Scores
    overall_score   = Column(Float, nullable=True)       # 0–10
    technical_score = Column(Float, nullable=True)
    communication_score = Column(Float, nullable=True)

    # Agent evaluation
    strengths       = Column(JSON, default=list)
    weaknesses      = Column(JSON, default=list)
    improvement_suggestions = Column(JSON, default=list)
    recommended_resources   = Column(JSON, default=list)

    scheduled_at    = Column(DateTime(timezone=True), nullable=True)
    completed_at    = Column(DateTime(timezone=True), nullable=True)
    created_at      = Column(DateTime(timezone=True), server_default=func.now())

    user            = relationship("User", back_populates="mock_interviews")


# ─── Skill Gap ────────────────────────────────────────────────────────────────

class SkillGap(Base):
    __tablename__ = "skill_gaps"

    id              = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    user_id         = Column(UUID(as_uuid=False), ForeignKey("users.id"))
    target_company  = Column(String(255), nullable=True)
    target_role     = Column(String(255), nullable=True)

    missing_skills  = Column(JSON, default=list)
    weak_subjects   = Column(JSON, default=list)
    missing_certs   = Column(JSON, default=list)
    missing_projects = Column(JSON, default=list)

    priority_order  = Column(JSON, default=list)  # Ordered list of what to fix first

    created_at      = Column(DateTime(timezone=True), server_default=func.now())


# ─── Learning History ─────────────────────────────────────────────────────────

class LearningHistory(Base):
    __tablename__ = "learning_history"

    id              = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    user_id         = Column(UUID(as_uuid=False), ForeignKey("users.id"))
    resource_type   = Column(
        Enum("video", "article", "doc", "sheet", "course", "problem", name="resource_type")
    )
    resource_title  = Column(String(500), nullable=False)
    resource_url    = Column(String(1000), nullable=True)
    topic           = Column(String(255), nullable=True)
    completed       = Column(Boolean, default=False)
    rating          = Column(Integer, nullable=True)  # Student rating 1–5
    completed_at    = Column(DateTime(timezone=True), nullable=True)
    created_at      = Column(DateTime(timezone=True), server_default=func.now())


# ─── Notifications ────────────────────────────────────────────────────────────

class Notification(Base):
    __tablename__ = "notifications"

    id              = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    user_id         = Column(UUID(as_uuid=False), ForeignKey("users.id"))
    title           = Column(String(255), nullable=False)
    message         = Column(Text, nullable=False)
    notification_type = Column(
        Enum("placement", "deadline", "interview", "roadmap",
             "assessment", "general", name="notification_type"),
        default="general"
    )
    is_read         = Column(Boolean, default=False)
    action_url      = Column(String(500), nullable=True)
    created_at      = Column(DateTime(timezone=True), server_default=func.now())

    user            = relationship("User", back_populates="notifications")
