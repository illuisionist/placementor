"""
Chat router — SSE streaming chat endpoint that runs the LangGraph agent graph.

Supports:
  - Regular chat (POST /chat/message)
  - Streaming chat (GET /chat/stream)
  - Chat history retrieval
"""

import json
import uuid
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional, AsyncGenerator

from database.session import get_db
from database.models import User
from auth import get_current_user
from memory.short_term import short_term_memory
from memory.long_term import long_term_memory
from agents.graph import run_graph

router = APIRouter(prefix="/chat", tags=["Chat"])


# ─── Schemas ─────────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    # Optional overrides for specialist agents
    interview_action: Optional[str] = None       # 'start' | 'answer' | 'evaluate'
    interview_type: Optional[str] = None
    target_company: Optional[str] = None
    target_role: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    intent: Optional[str]
    suggested_next_action: Optional[str]
    session_id: str
    sources: Optional[list] = None


# ─── Endpoints ───────────────────────────────────────────────────────────────

@router.post("/message", response_model=ChatResponse)
async def chat_message(
    payload: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Send a message to PlaceMentor AI and receive a response.
    Runs the full LangGraph agent pipeline.
    """
    user_id = str(current_user.id)
    session_id = payload.session_id or str(uuid.uuid4())

    # Load memory
    chat_history = await short_term_memory.get_chat_history(user_id)
    student_context = await long_term_memory.get_student_context(db, user_id)
    interview_state = await short_term_memory.get_interview_state(user_id)

    # Build extra state for specialist agents
    extra_state = {}
    if interview_state:
        extra_state["_interview_state"] = interview_state
    if payload.interview_action:
        extra_state["_interview_action"] = payload.interview_action
    if payload.interview_type:
        extra_state["_interview_type"] = payload.interview_type
    if payload.target_company:
        extra_state["_target_company"] = payload.target_company

    # Run agent graph
    final_state = await run_graph(
        user_id=user_id,
        session_id=session_id,
        user_message=payload.message,
        chat_history=chat_history,
        student_context=student_context,
        extra_state=extra_state,
    )

    response_text = final_state.get("final_response") or "I'm here to help with your placement journey!"

    # Persist to short-term memory
    await short_term_memory.append_message(user_id, "user", payload.message)
    await short_term_memory.append_message(user_id, "assistant", response_text)

    # Persist interview state if active
    if final_state.get("_interview_state"):
        await short_term_memory.set_interview_state(user_id, final_state["_interview_state"])

    # Persist roadmap/skill gaps to DB if generated
    if final_state.get("roadmap"):
        await _save_roadmap(db, user_id, final_state["roadmap"], payload.target_company, payload.target_role)

    if final_state.get("skill_gap"):
        await _save_skill_gap(db, user_id, final_state["skill_gap"])

    if final_state.get("resume_review"):
        await _save_resume_review(db, user_id, final_state["resume_review"])

    return ChatResponse(
        response=response_text,
        intent=final_state.get("intent"),
        suggested_next_action=final_state.get("suggested_next_action"),
        session_id=session_id,
        sources=final_state.get("retrieved_sources", [])[:3],  # Return top 3 sources
    )


@router.get("/history")
async def get_chat_history(
    current_user: User = Depends(get_current_user),
    last_n: int = 20,
):
    """Get recent chat history for the current session."""
    history = await short_term_memory.get_chat_history(str(current_user.id), last_n=last_n)
    return {"messages": history}


@router.delete("/history")
async def clear_chat_history(
    current_user: User = Depends(get_current_user),
):
    """Clear the chat history and interview state for the student."""
    user_id = str(current_user.id)
    await short_term_memory.clear_chat_history(user_id)
    await short_term_memory.clear_interview_state(user_id)
    return {"message": "Chat history cleared"}


# ─── SSE Streaming Endpoint ──────────────────────────────────────────────────

@router.post("/stream")
async def chat_stream(
    payload: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Streaming version of chat — uses Server-Sent Events.
    Frontend can use EventSource or fetch with ReadableStream.
    """
    user_id = str(current_user.id)
    session_id = payload.session_id or str(uuid.uuid4())

    chat_history = await short_term_memory.get_chat_history(user_id)
    student_context = await long_term_memory.get_student_context(db, user_id)

    async def event_generator() -> AsyncGenerator[str, None]:
        # Send intent event first (from fast planner)
        yield f"data: {json.dumps({'type': 'status', 'content': 'Analyzing your request...'})}\n\n"

        try:
            final_state = await run_graph(
                user_id=user_id,
                session_id=session_id,
                user_message=payload.message,
                chat_history=chat_history,
                student_context=student_context,
            )

            response_text = final_state.get("final_response", "")

            # Stream response word by word (simulate streaming)
            words = response_text.split(" ")
            buffer = ""
            for i, word in enumerate(words):
                buffer += word + (" " if i < len(words) - 1 else "")
                if len(buffer) > 10 or i == len(words) - 1:
                    yield f"data: {json.dumps({'type': 'token', 'content': buffer})}\n\n"
                    buffer = ""

            # Send metadata
            yield f"data: {json.dumps({'type': 'meta', 'intent': final_state.get('intent'), 'next_action': final_state.get('suggested_next_action')})}\n\n"
            yield f"data: {json.dumps({'type': 'done'})}\n\n"

            # Save to memory
            await short_term_memory.append_message(user_id, "user", payload.message)
            await short_term_memory.append_message(user_id, "assistant", response_text)

            # Persist interview state if active
            if final_state.get("_interview_state"):
                await short_term_memory.set_interview_state(user_id, final_state["_interview_state"])

            # Persist roadmap/skill gaps to DB if generated
            if final_state.get("roadmap"):
                await _save_roadmap(db, user_id, final_state["roadmap"], payload.target_company, payload.target_role)

            if final_state.get("skill_gap"):
                await _save_skill_gap(db, user_id, final_state["skill_gap"])

            if final_state.get("resume_review"):
                await _save_resume_review(db, user_id, final_state["resume_review"])

            await db.commit()

        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


# ─── DB Persistence Helpers ───────────────────────────────────────────────────

async def _save_roadmap(db, user_id: str, roadmap: dict, target_company: str = None, target_role: str = None):
    """Persist generated roadmap to the database."""
    from sqlalchemy import update
    from database.models import Roadmap
    # Deactivate old roadmap
    await db.execute(update(Roadmap).where(Roadmap.user_id == user_id).values(is_active=False))
    new_roadmap = Roadmap(
        user_id=user_id,
        title=roadmap.get("title", "Placement Roadmap"),
        target_company=target_company or roadmap.get("target_company"),
        target_role=target_role or roadmap.get("target_role"),
        duration_weeks=roadmap.get("duration_weeks", 8),
        weeks_plan=roadmap.get("weeks", []),
        is_active=True,
    )
    db.add(new_roadmap)
    await db.commit()


async def _save_skill_gap(db, user_id: str, skill_gap: dict):
    """Persist skill gap snapshot to the database."""
    from database.models import SkillGap
    sg = SkillGap(
        user_id=user_id,
        target_company=skill_gap.get("target_company"),
        target_role=skill_gap.get("target_role"),
        missing_skills=[s.get("skill") for s in skill_gap.get("missing_skills", [])],
        weak_subjects=[s.get("subject") for s in skill_gap.get("weak_subjects", [])],
        missing_certs=skill_gap.get("missing_certifications", []),
        priority_order=skill_gap.get("priority_action_plan", []),
    )
    db.add(sg)
    await db.commit()


async def _save_resume_review(db, user_id: str, review: dict):
    """Update ATS score on the most recent active resume."""
    from sqlalchemy import update
    from database.models import Resume
    active_resume = await long_term_memory.get_active_resume(db, user_id)
    if active_resume:
        await db.execute(
            update(Resume)
            .where(Resume.id == active_resume.id)
            .values(
                ats_score=review.get("ats_score"),
                strengths=review.get("strengths", []),
                weaknesses=review.get("weaknesses", []),
                suggestions=review.get("suggestions", []),
                raw_review=str(review),
            )
        )
        await db.commit()
