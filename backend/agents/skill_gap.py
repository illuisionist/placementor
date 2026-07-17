"""
Skill Gap Agent — compares student profile with company requirements.

Uses RAG-retrieved company JD context + student profile to identify
missing skills, weak subjects, and missing certifications.
"""

import json
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from agents.state import AgentState
from agents.llm_factory import get_groq_llm
from loguru import logger

SKILL_GAP_SYSTEM = """You are the Skill Gap Analyst for PlaceMentor AI.

Compare the student's current profile with the target company's requirements.
Be specific, honest, and prioritize recommendations by placement importance.

Student Profile:
{student_context}

Company/Role Requirements (from knowledge base):
{company_context}

Respond ONLY with valid JSON:
{{
    "target_company": "<company name>",
    "target_role": "<role>",
    "readiness_score": <0-100>,
    "eligible": true/false,
    "eligibility_reason": "<why eligible or not>",
    "missing_skills": [
        {{"skill": "<skill>", "importance": "critical|high|medium", "estimated_learning_time": "<X weeks>"}}
    ],
    "weak_subjects": [
        {{"subject": "<subject>", "importance": "critical|high|medium", "current_level": "beginner|intermediate"}}
    ],
    "missing_certifications": ["<cert1>", ...],
    "missing_project_types": ["<project type>", ...],
    "priority_action_plan": ["<action 1>", "<action 2>", ...],
    "summary": "<2-3 sentence summary>"
}}"""

SKILL_GAP_USER = """Analyze skill gap for:
Target Company: {target_company}
Target Role: {target_role}

What skills/experience does this student need to acquire?"""


async def skill_gap_agent(state: AgentState, target_company: str = "",
                           target_role: str = "") -> AgentState:
    """LangGraph node: Skill Gap Agent."""
    llm = get_groq_llm()

    student_ctx = json.dumps(state.get("student_context") or {}, indent=2)
    company_context = state.get("retrieved_context") or "No specific company information retrieved."

    # Try to extract target from student preferences if not provided
    if not target_company:
        prefs = (state.get("student_context") or {}).get("profile", {})
        companies = prefs.get("preferred_companies", [])
        target_company = companies[0] if companies else "top product companies"

    if not target_role:
        domains = (state.get("student_context") or {}).get("profile", {}).get("preferred_domains", [])
        target_role = domains[0] if domains else "Software Development Engineer"

    prompt = ChatPromptTemplate.from_messages([
        ("system", SKILL_GAP_SYSTEM),
        ("human", SKILL_GAP_USER),
    ])

    chain = prompt | llm | JsonOutputParser()

    try:
        result = await chain.ainvoke({
            "student_context": student_ctx,
            "company_context": company_context,
            "target_company": target_company,
            "target_role": target_role,
        })

        logger.info(f"[SkillGap] Readiness: {result.get('readiness_score')}% for {target_company}")

        critical_skills = [s for s in result.get("missing_skills", []) if s.get("importance") == "critical"]
        high_skills = [s for s in result.get("missing_skills", []) if s.get("importance") == "high"]

        response = (
            f"🎯 **Skill Gap Analysis — {target_company} ({target_role})**\n\n"
            f"**Placement Readiness**: {result.get('readiness_score', 'N/A')}%\n"
            f"**Eligibility**: {'✅ Eligible' if result.get('eligible') else '❌ Not yet eligible'}\n"
            f"{result.get('eligibility_reason', '')}\n\n"
            f"**Summary**: {result.get('summary', '')}\n\n"
        )

        if critical_skills:
            response += "**🔴 Critical Missing Skills**:\n" + "\n".join(
                f"• {s['skill']} (~{s.get('estimated_learning_time', 'N/A')} to learn)"
                for s in critical_skills
            ) + "\n\n"

        if high_skills:
            response += "**🟡 High Priority Skills**:\n" + "\n".join(
                f"• {s['skill']}" for s in high_skills[:4]
            ) + "\n\n"

        if result.get("weak_subjects"):
            response += "**📚 Subjects to Strengthen**:\n" + "\n".join(
                f"• {s['subject']} (currently: {s.get('current_level', 'unknown')})"
                for s in result.get("weak_subjects", [])[:4]
            ) + "\n\n"

        response += "**✅ Priority Action Plan**:\n" + "\n".join(
            f"{i+1}. {action}"
            for i, action in enumerate(result.get("priority_action_plan", [])[:5])
        )

        return {
            **state,
            "skill_gap": result,
            "final_response": response,
            "suggested_next_action": "Would you like me to create a personalized preparation roadmap based on these gaps?",
        }

    except Exception as e:
        logger.error(f"[SkillGap] Failed: {e}")
        return {
            **state,
            "error": f"Skill gap analysis failed: {str(e)}",
            "final_response": "I couldn't complete the skill gap analysis. Please try again.",
        }
