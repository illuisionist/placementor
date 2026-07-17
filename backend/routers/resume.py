"""
Resume upload router — handles file upload, text extraction, and triggers resume workflow.
"""

import os
import uuid
import aiofiles
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update

from database.session import get_db
from database.models import User, Resume
from auth import get_current_user
from config import settings
from memory.long_term import long_term_memory

router = APIRouter(prefix="/resume", tags=["Resume"])

ALLOWED_TYPES = {"application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"}
ALLOWED_EXTENSIONS = {".pdf", ".docx"}


async def extract_text(file_path: str) -> str:
    """Extract text from PDF or DOCX file."""
    ext = os.path.splitext(file_path)[1].lower()
    try:
        if ext == ".pdf":
            from langchain_community.document_loaders import PyPDFLoader
            loader = PyPDFLoader(file_path)
            docs = loader.load()
            return "\n".join(d.page_content for d in docs)
        elif ext == ".docx":
            import docx2txt
            return docx2txt.process(file_path)
    except Exception as e:
        return f"[Text extraction failed: {e}]"
    return ""


@router.post("/upload")
async def upload_resume(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload a resume (PDF or DOCX).
    Saves file, extracts text, deactivates old resumes, and stores in DB.
    """
    # Validate file type
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(400, detail=f"Only PDF and DOCX files are supported. Got: {ext}")

    # Validate file size
    content = await file.read()
    if len(content) > settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024:
        raise HTTPException(400, detail=f"File too large. Max size: {settings.MAX_UPLOAD_SIZE_MB}MB")

    # Save file
    user_id = str(current_user.id)
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    filename = f"{user_id}_{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(settings.UPLOAD_DIR, filename)

    async with aiofiles.open(file_path, "wb") as f:
        await f.write(content)

    # Extract text
    text = await extract_text(file_path)

    # Get next version number
    old_resumes = await long_term_memory.get_all_resumes(db, user_id)
    version = max((r.version for r in old_resumes), default=0) + 1

    # Deactivate previous resumes
    await db.execute(update(Resume).where(Resume.user_id == user_id).values(is_active=False))

    # Save new resume record
    resume = Resume(
        user_id=user_id,
        file_path=file_path,
        original_name=file.filename,
        version=version,
        is_active=True,
    )
    db.add(resume)
    await db.flush()

    return {
        "message": "Resume uploaded successfully!",
        "resume_id": resume.id,
        "version": version,
        "file_name": file.filename,
        "text_length": len(text),
        "next_step": "Use the chat to ask 'Review my resume' and I'll analyze it for ATS compatibility and improvement suggestions.",
        "_extracted_text_preview": text[:300] + "..." if len(text) > 300 else text,
    }


@router.get("/list")
async def list_resumes(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all resume versions for the student."""
    resumes = await long_term_memory.get_all_resumes(db, str(current_user.id))
    return [
        {
            "id": r.id,
            "version": r.version,
            "original_name": r.original_name,
            "is_active": r.is_active,
            "ats_score": r.ats_score,
            "uploaded_at": r.uploaded_at,
        }
        for r in resumes
    ]
