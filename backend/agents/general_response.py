"""
General Response Agent — answers placement Q&A using RAG context + LLM.
Used for any intent that doesn't require a specialist agent.
"""

import json
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from agents.state import AgentState
from agents.llm_factory import get_groq_llm

GENERAL_SYSTEM = """You are PlaceMentor AI, an intelligent placement mentor for LPU (Lovely Professional University) students.

You are supportive, professional, encouraging, and concise.

Rules:
- ONLY answer placement-related questions.
- Use the retrieved knowledge base context when available — cite sources.
- NEVER fabricate placement statistics, company policies, or eligibility criteria.
- If you don't know, say so clearly.
- Always suggest a clear next action for the student.
- Keep responses focused and actionable.

Student context:
{student_context}

Knowledge Base Context:
{kb_context}

Chat history (last 3 exchanges):
{chat_history}"""

GENERAL_USER = "{user_message}"


async def general_response_agent(state: AgentState) -> AgentState:
    """LangGraph node: General Response Agent (fallback for Q&A)."""
    llm = get_groq_llm()

    student_ctx = json.dumps(state.get("student_context") or {}, indent=2)
    kb_context = state.get("retrieved_context") or "No specific information retrieved."

    history_str = "\n".join(
        f"{m['role'].upper()}: {m['content']}"
        for m in (state.get("chat_history") or [])[-6:]
    ) or "No previous conversation."

    prompt = ChatPromptTemplate.from_messages([
        ("system", GENERAL_SYSTEM),
        ("human", GENERAL_USER),
    ])

    chain = prompt | llm | StrOutputParser()

    response = await chain.ainvoke({
        "student_context": student_ctx,
        "kb_context": kb_context,
        "chat_history": history_str,
        "user_message": state["user_message"],
    })

    return {
        **state,
        "final_response": response,
        "suggested_next_action": "Is there anything specific you'd like me to help you with — resume review, mock interview, or roadmap?",
    }
