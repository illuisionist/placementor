"""
Agent State — shared TypedDict used across the LangGraph graph.

All agents read from and write to this state object.
LangGraph merges state updates after each node execution.
"""

from typing import Annotated, Any, Optional
from typing_extensions import TypedDict
import operator


class AgentState(TypedDict):
    # ── Core Identity ─────────────────────────────────────────────────────────
    user_id: str
    session_id: str

    # ── Conversation ──────────────────────────────────────────────────────────
    user_message: str                          # Current user input
    chat_history: list[dict]                   # [{role, content}, ...]
    # Reducer: append new messages
    messages: Annotated[list[dict], operator.add]

    # ── Routing ───────────────────────────────────────────────────────────────
    intent: Optional[str]                      # Detected intent from Planner
    next_agent: Optional[str]                  # Which agent to call next
    sub_tasks: list[str]                       # Planner-decomposed subtasks

    # ── Student Context ───────────────────────────────────────────────────────
    student_context: Optional[dict]            # From long_term_memory.get_student_context()

    # ── Retrieved Context ─────────────────────────────────────────────────────
    retrieved_context: Optional[str]           # Formatted RAG context
    retrieved_sources: list[dict]              # Raw source chunks with metadata

    # ── Agent Outputs ─────────────────────────────────────────────────────────
    resume_review: Optional[dict]              # From ResumeReviewAgent
    skill_gap: Optional[dict]                  # From SkillGapAgent
    roadmap: Optional[dict]                    # From RoadmapAgent
    learning_resources: Optional[list]        # From LearningRecommendationAgent
    interview_result: Optional[dict]           # From MockInterviewAgent
    progress_report: Optional[dict]            # From ProgressTrackingAgent

    # ── Final Response ────────────────────────────────────────────────────────
    final_response: Optional[str]              # The response to stream back to user
    suggested_next_action: Optional[str]       # What the system suggests the student do next

    # ── Error Handling ────────────────────────────────────────────────────────
    error: Optional[str]
