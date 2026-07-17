"""
Planner Agent — the router/orchestrator of the LangGraph graph.

Responsibilities:
  - Understand what the student wants.
  - Detect intent (resume review, mock interview, roadmap, Q&A, etc.)
  - Break the task into sub-tasks.
  - Set next_agent to route to the right specialist.

This runs FIRST in every graph execution.
"""

import json
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from agents.state import AgentState
from agents.llm_factory import get_groq_fast_llm
from loguru import logger

# ─── Supported Intents ────────────────────────────────────────────────────────

INTENT_MAP = {
    "resume_review":        "Student wants resume analyzed or improved.",
    "skill_gap":            "Student wants to know missing skills for a company/role.",
    "roadmap":              "Student wants a personalized preparation plan.",
    "mock_interview":       "Student wants to start or continue a mock interview.",
    "learning_resources":  "Student wants study material, videos, or resources.",
    "progress":             "Student wants to check their preparation progress.",
    "company_info":         "Student is asking about a specific company's hiring process.",
    "placement_policy":     "Student is asking about LPU placement rules/eligibility.",
    "general_qa":           "General placement-related question.",
    "profile_update":       "Student wants to update their profile/skills/details.",
}

# ─── System Prompt ────────────────────────────────────────────────────────────

PLANNER_SYSTEM = """You are the Planner Agent for PlaceMentor AI — an intelligent placement mentorship 
system for LPU students.

Your job is to analyze the student's message and output a structured routing plan.

Available intents: {intent_list}

Student context summary:
{student_context}

Respond ONLY with valid JSON. No extra text. Format:
{{
    "intent": "<one of the intent keys above>",
    "sub_tasks": ["<task1>", "<task2>"],
    "needs_retrieval": true/false,
    "retrieval_query": "<optional search query for the RAG system>",
    "next_agent": "<agent to call: retrieval_agent | resume_review_agent | skill_gap_agent | roadmap_agent | mock_interview_agent | learning_agent | general_response>",
    "reasoning": "<brief explanation of your routing decision>"
}}
"""

PLANNER_USER = """Chat history:
{chat_history}

Current student message: {user_message}"""

# ─── Planner Node ─────────────────────────────────────────────────────────────

async def planner_agent(state: AgentState) -> AgentState:
    """
    LangGraph node: Planner Agent.
    Analyzes intent and decides which specialist agent to call next.
    """
    llm = get_groq_fast_llm()

    intent_list = "\n".join([f"  - {k}: {v}" for k, v in INTENT_MAP.items()])
    student_ctx = json.dumps(state.get("student_context") or {}, indent=2)

    # Format chat history
    history_str = "\n".join(
        f"{m['role'].upper()}: {m['content']}"
        for m in (state.get("chat_history") or [])[-6:]  # Last 3 exchanges
    ) or "No previous conversation."

    prompt = ChatPromptTemplate.from_messages([
        ("system", PLANNER_SYSTEM),
        ("human", PLANNER_USER),
    ])

    chain = prompt | llm | JsonOutputParser()

    try:
        result = await chain.ainvoke({
            "intent_list": intent_list,
            "student_context": student_ctx,
            "chat_history": history_str,
            "user_message": state["user_message"],
        })

        logger.info(f"[Planner] Intent: {result.get('intent')} → {result.get('next_agent')}")

        return {
            **state,
            "intent": result.get("intent", "general_qa"),
            "sub_tasks": result.get("sub_tasks", []),
            "next_agent": result.get("next_agent", "general_response"),
            # Store retrieval query for retrieval agent
            "_retrieval_query": result.get("retrieval_query", state["user_message"]),
            "_needs_retrieval": result.get("needs_retrieval", False),
        }

    except Exception as e:
        logger.error(f"[Planner] Failed to parse intent: {e}")
        return {
            **state,
            "intent": "general_qa",
            "next_agent": "general_response",
            "error": f"Planner error: {str(e)}",
        }


# ─── Router Function (used by LangGraph conditional_edge) ─────────────────────

def route_after_planner(state: AgentState) -> str:
    """
    LangGraph conditional edge — returns the name of the next node.
    """
    needs_retrieval = state.get("_needs_retrieval", False)
    next_agent = state.get("next_agent", "general_response")

    # Always retrieve first if needed
    if needs_retrieval:
        return "retrieval_agent"

    # Safety: if LLM returns an agent name that doesn't exist in the graph, fallback
    valid_agents = {
        "retrieval_agent", "resume_review_agent", "skill_gap_agent",
        "roadmap_agent", "mock_interview_agent", "learning_agent", "general_response",
    }
    if next_agent not in valid_agents:
        logger.warning(f"[Planner] Unknown next_agent '{next_agent}', falling back to general_response")
        return "general_response"

    return next_agent
