"""
Retrieval Agent — queries Pinecone and injects relevant context into state.

Runs before other agents when the planner determines retrieval is needed.
"""

from agents.state import AgentState
from rag.vector_store import query_collection, query_all_namespaces
from loguru import logger

# ─── Intent → Pinecone Namespace Mapping (inline in retrieval_agent) ─────────


async def retrieval_agent(state: AgentState) -> AgentState:
    """
    LangGraph node: Retrieval Agent.
    Selects the right collection, retrieves relevant chunks, formats context.
    """
    intent = state.get("intent", "general_qa")
    query = state.get("_retrieval_query") or state["user_message"]

    # Determine which Pinecone namespace to search
    INTENT_TO_NS = {
        "placement_policy":   "general",
        "company_info":       "company_profiles",
        "mock_interview":     "interview_experiences",
        "learning_resources": "general",
        "skill_gap":          "company_profiles",
        "roadmap":            "general",
        "general_qa":         "general",
    }
    namespace = INTENT_TO_NS.get(intent, "general")

    logger.info(f"[Retrieval] Query: '{query[:60]}' → Namespace: {namespace}")

    if intent in ("resume_review", "profile_update"):
        return {**state, "retrieved_context": "", "retrieved_sources": []}

    if intent == "company_info":
        results = query_all_namespaces(query, top_k=3)
    else:
        results = query_collection(query, namespace=namespace, top_k=5)

    if not results:
        logger.warning(f"[Retrieval] No results for: {query[:60]}")
        context = "No specific information was found in the knowledge base."
    else:
        context_parts = []
        for i, r in enumerate(results, 1):
            score_str = f" (relevance: {r['score']:.2f})" if r.get("score") else ""
            context_parts.append(
                f"[Source {i} — {r.get('source', 'KB')}{score_str}]\n{r['text']}"
            )
        context = "\n\n---\n\n".join(context_parts)

    logger.info(f"[Retrieval] Retrieved {len(results)} chunks")

    return {
        **state,
        "retrieved_context": context,
        "retrieved_sources": results,
    }


def route_after_retrieval(state: AgentState) -> str:
    """
    After retrieval, continue to the originally planned agent.
    """
    return state.get("next_agent", "general_response")
