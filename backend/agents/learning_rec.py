"""
Learning Recommendation Agent — suggests curated resources based on roadmap & gaps.
"""

import json
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from agents.state import AgentState
from agents.llm_factory import get_groq_llm
from rag.retriever import retrieve_learning_resources
from loguru import logger

LEARNING_SYSTEM = """You are the Learning Recommendation Agent for PlaceMentor AI.

Your job is to recommend the BEST, most specific, and free learning resources
for the student's current preparation needs.

Prioritize:
1. Free resources (YouTube, GeeksforGeeks, NeetCode, LeetCode, etc.)
2. Resources matching the student's current roadmap week
3. Resources that address identified skill gaps
4. Company-specific resources when targeting specific companies

Student context:
{student_context}

Current roadmap status:
{roadmap_context}

Skill gaps:
{skill_gaps}

Additional context from knowledge base:
{kb_context}

Respond ONLY with valid JSON:
{{
    "recommendations": [
        {{
            "topic": "<topic>",
            "resource_type": "video|article|practice|course|sheet",
            "title": "<resource title>",
            "url": "<resource URL>",
            "why": "<why this resource>",
            "estimated_time": "<X hours/days>",
            "priority": "high|medium|low"
        }}
    ],
    "weekly_plan": {{
        "monday_wednesday_friday": "<what to study>",
        "tuesday_thursday": "<what to practice>",
        "saturday_sunday": "<what to review/project>"
    }},
    "quick_wins": ["<resource that gives immediate impact>"],
    "deep_dives": ["<resource for comprehensive learning>"]
}}"""

LEARNING_USER = "What should I study for {topic}?"


async def learning_recommendation_agent(state: AgentState, topic: str = "") -> AgentState:
    """LangGraph node: Learning Recommendation Agent."""
    llm = get_groq_llm()

    student_ctx = json.dumps(state.get("student_context") or {}, indent=2)
    roadmap = state.get("roadmap") or {}
    skill_gap = state.get("skill_gap") or {}

    # Determine topic from roadmap current week or skill gaps
    if not topic:
        skill_gaps_list = skill_gap.get("missing_skills", [])
        topic = skill_gaps_list[0].get("skill", "DSA") if skill_gaps_list else "Data Structures and Algorithms"

    # Retrieve from knowledge base
    kb_results = retrieve_learning_resources(topic, top_k=4)
    kb_context = "\n\n".join(r["content"] for r in kb_results) if kb_results else "No KB resources found."

    roadmap_ctx = ""
    if roadmap:
        current_week = roadmap.get("weeks", [{}])[0] if roadmap.get("weeks") else {}
        roadmap_ctx = f"Current week theme: {current_week.get('theme', 'N/A')}\nGoals: {current_week.get('goals', [])}"

    prompt = ChatPromptTemplate.from_messages([
        ("system", LEARNING_SYSTEM),
        ("human", LEARNING_USER),
    ])

    chain = prompt | llm | JsonOutputParser()

    try:
        result = await chain.ainvoke({
            "student_context": student_ctx,
            "roadmap_context": roadmap_ctx or "No active roadmap.",
            "skill_gaps": json.dumps(skill_gap, indent=2),
            "kb_context": kb_context,
            "topic": topic,
        })

        recs = result.get("recommendations", [])
        high_priority = [r for r in recs if r.get("priority") == "high"]
        other = [r for r in recs if r.get("priority") != "high"]

        response = f"📚 **Learning Resources for: {topic}**\n\n"

        if high_priority:
            response += "**🔴 Start with these (High Priority)**:\n"
            for r in high_priority[:3]:
                response += (
                    f"• **{r['title']}** ({r['resource_type']}) — ⏱ {r.get('estimated_time', 'N/A')}\n"
                    f"  → {r.get('why', '')}\n"
                    f"  🔗 {r.get('url', 'Search on YouTube/Google')}\n\n"
                )

        if other:
            response += "**📘 Additional Resources**:\n"
            for r in other[:3]:
                response += f"• {r['title']} ({r['resource_type']}) — {r.get('url', 'Google it')}\n"

        if result.get("quick_wins"):
            response += "\n**⚡ Quick Wins** (study today):\n" + "\n".join(
                f"• {qw}" for qw in result["quick_wins"][:2]
            )

        return {
            **state,
            "learning_resources": recs,
            "final_response": response,
            "suggested_next_action": f"After studying {topic}, take a quick quiz or attempt related LeetCode problems to solidify your learning.",
        }

    except Exception as e:
        logger.error(f"[LearningRec] Failed: {e}")
        return {
            **state,
            "error": str(e),
            "final_response": "I couldn't generate resource recommendations right now.",
        }
