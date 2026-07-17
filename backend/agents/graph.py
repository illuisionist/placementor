"""
LangGraph Orchestrator — assembles all agents into a stateful graph.

Graph flow:
  User message
      ↓
  [planner_agent]     — detect intent, set next_agent
      ↓ (conditional)
  [retrieval_agent]   — fetch relevant context (if needed)
      ↓ (conditional)
  [specialist agent]  — resume_review | skill_gap | roadmap | mock_interview | learning | general
      ↓
  END

All state is persisted across turns via the AgentState TypedDict.
"""

from langgraph.graph import StateGraph, END, START
from agents.state import AgentState
from agents.planner import planner_agent, route_after_planner
from agents.retrieval import retrieval_agent, route_after_retrieval
from agents.resume_review import resume_review_agent
from agents.skill_gap import skill_gap_agent
from agents.roadmap import roadmap_agent
from agents.mock_interview import mock_interview_agent
from agents.learning_rec import learning_recommendation_agent
from agents.general_response import general_response_agent


# ─── Build Graph ─────────────────────────────────────────────────────────────

def build_graph() -> StateGraph:
    builder = StateGraph(AgentState)

    # ── Nodes ────────────────────────────────────────────────────────────────
    builder.add_node("planner_agent", planner_agent)
    builder.add_node("retrieval_agent", retrieval_agent)
    builder.add_node("resume_review_agent", resume_review_agent)
    builder.add_node("skill_gap_agent", skill_gap_agent)
    builder.add_node("roadmap_agent", roadmap_agent)
    builder.add_node("mock_interview_agent", mock_interview_agent)
    builder.add_node("learning_agent", learning_recommendation_agent)
    builder.add_node("general_response", general_response_agent)

    # ── Entry Point (LangGraph 0.2.x compatible) ─────────────────────────────
    builder.add_edge(START, "planner_agent")

    # ── Conditional Edge: Planner → next ─────────────────────────────────────
    builder.add_conditional_edges(
        "planner_agent",
        route_after_planner,
        {
            "retrieval_agent":      "retrieval_agent",
            "resume_review_agent":  "resume_review_agent",
            "skill_gap_agent":      "skill_gap_agent",
            "roadmap_agent":        "roadmap_agent",
            "mock_interview_agent": "mock_interview_agent",
            "learning_agent":       "learning_agent",
            "general_response":     "general_response",
        },
    )

    # ── Conditional Edge: Retrieval → intended specialist ────────────────────
    builder.add_conditional_edges(
        "retrieval_agent",
        route_after_retrieval,
        {
            "resume_review_agent":  "resume_review_agent",
            "skill_gap_agent":      "skill_gap_agent",
            "roadmap_agent":        "roadmap_agent",
            "mock_interview_agent": "mock_interview_agent",
            "learning_agent":       "learning_agent",
            "general_response":     "general_response",
        },
    )

    # ── Terminal Edges (all specialists → END) ────────────────────────────────
    for node in [
        "resume_review_agent",
        "skill_gap_agent",
        "roadmap_agent",
        "mock_interview_agent",
        "learning_agent",
        "general_response",
    ]:
        builder.add_edge(node, END)

    return builder.compile()


# Compiled graph — import this in routers
graph = build_graph()


# ─── Run Helper ──────────────────────────────────────────────────────────────

async def run_graph(
    user_id: str,
    session_id: str,
    user_message: str,
    chat_history: list[dict] = None,
    student_context: dict = None,
    extra_state: dict = None,
) -> AgentState:
    """
    Run the full agent graph for a user message.
    Returns the final state.
    """
    initial_state: AgentState = {
        "user_id": user_id,
        "session_id": session_id,
        "user_message": user_message,
        "chat_history": chat_history or [],
        "messages": [],
        "intent": None,
        "next_agent": None,
        "sub_tasks": [],
        "student_context": student_context,
        "retrieved_context": None,
        "retrieved_sources": [],
        "resume_review": None,
        "skill_gap": None,
        "roadmap": None,
        "learning_resources": None,
        "interview_result": None,
        "progress_report": None,
        "final_response": None,
        "suggested_next_action": None,
        "error": None,
        **(extra_state or {}),
    }

    final_state = await graph.ainvoke(initial_state)
    return final_state
