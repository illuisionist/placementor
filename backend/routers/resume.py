"""
Resume upload router — handles file upload, text extraction, and triggers resume workflow.
"""

import os
import uuid
import asyncio
import aiofiles
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update

from database.session import get_db
from database.models import User, Resume
from auth import get_current_user
from config import settings
from memory.long_term import long_term_memory
from agents.llm_factory import get_groq_llm
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

router = APIRouter(prefix="/resume", tags=["Resume"])

ALLOWED_TYPES = {"application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"}
ALLOWED_EXTENSIONS = {".pdf", ".docx"}


async def _run_ats_analysis(resume_id: str, extracted_text: str):
    """Background task: Run ATS analysis on uploaded resume."""
    from database.session import AsyncSessionLocal
    try:
        llm = get_groq_llm()
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert ATS (Applicant Tracking System) resume analyzer.
Analyze the following resume text and provide a detailed evaluation.

Respond ONLY with valid JSON:
{{
    "ats_score": <number 0-100>,
    "strengths": ["<strength1>", "<strength2>", ...],
    "weaknesses": ["<weakness1>", "<weakness2>", ...],
    "suggestions": [
        {{"priority": "HIGH", "suggestion": "<text>", "fix": "<how to fix>"}},
        {{"priority": "MEDIUM", "suggestion": "<text>", "fix": "<how to fix>"}},
        {{"priority": "LOW", "suggestion": "<text>", "fix": "<how to fix>"}}
    ]
}}"""),
            ("human", "Resume text:\n{resume_text}")
        ])
        chain = prompt | llm | JsonOutputParser()
        result = await chain.ainvoke({"resume_text": extracted_text[:4000]})

        async with AsyncSessionLocal() as db:
            from database.models import Resume
            from sqlalchemy import update
            await db.execute(
                update(Resume).where(Resume.id == resume_id).values(
                    ats_score=result.get("ats_score"),
                    strengths=result.get("strengths", []),
                    weaknesses=result.get("weaknesses", []),
                    suggestions=result.get("suggestions", []),
                    raw_review=str(result),
                )
            )
            await db.commit()
    except Exception as e:
        from loguru import logger
        logger.error(f"ATS analysis failed for resume {resume_id}: {e}")


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
    Triggers automatic ATS analysis in the background.
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

    # Store extracted text on the resume record
    resume.extracted_text = text
    await db.commit()

    # Trigger background ATS analysis
    asyncio.create_task(_run_ats_analysis(str(resume.id), text))

    return {
        "message": "Resume uploaded successfully!",
        "resume_id": str(resume.id),
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
            "strengths": r.strengths or [],
            "weaknesses": r.weaknesses or [],
            "suggestions": r.suggestions or [],
            "uploaded_at": r.uploaded_at,
        }
        for r in resumes
    ]
