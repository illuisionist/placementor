"""
Resume Review Agent — analyzes resume text using Gemini (large context).

Evaluates ATS compatibility, formatting, grammar, projects, impact, and readability.
Returns structured JSON with scores and improvement suggestions.
"""

import json
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from agents.state import AgentState
from agents.llm_factory import get_gemini_llm
from loguru import logger

RESUME_REVIEW_SYSTEM = """You are an expert resume reviewer and ATS specialist for campus placements.
You are helping a student from LPU (Lovely Professional University) improve their resume.

Analyze the provided resume text and return a structured evaluation.

Your evaluation criteria:
1. ATS Compatibility: Keywords, formatting, standard section headers
2. Formatting: Consistency, readability, length appropriateness
3. Grammar & Language: Correctness, professional tone, active voice
4. Project Quality: Technical depth, measurable outcomes, relevance
5. Technical Skills: Relevance to student's target role
6. Impact & Achievements: Quantified results (%, numbers, metrics)
7. Consistency: Dates, formatting, bullet style
8. Missing Sections: What important sections are missing

Student context:
{student_context}

Respond ONLY with valid JSON:
{{
    "ats_score": <0-100>,
    "overall_score": <0-10>,
    "strengths": ["<strength1>", "<strength2>", ...],
    "weaknesses": ["<weakness1>", "<weakness2>", ...],
    "suggestions": [
        {{
            "category": "<category>",
            "issue": "<what is wrong>",
            "fix": "<specific fix suggestion>",
            "priority": "<high|medium|low>"
        }}
    ],
    "missing_sections": ["<section1>", ...],
    "keywords_to_add": ["<keyword1>", ...],
    "summary": "<2-3 sentence overall assessment>"
}}"""

RESUME_REVIEW_USER = """Please review this resume:

{resume_text}

The student is targeting: {target_role} at {target_company}"""


async def resume_review_agent(state: AgentState, resume_text: str = None,
                               target_role: str = "", target_company: str = "") -> AgentState:
    """
    LangGraph node: Resume Review Agent.
    Uses Gemini for large-context resume analysis.
    """
    llm = get_gemini_llm()

    student_ctx = json.dumps(state.get("student_context") or {}, indent=2)
    
    # Try to get resume text: first from explicit override, then from student_context
    resume = resume_text or state.get("_resume_text")
    if not resume:
        ctx = state.get("student_context") or {}
        resume = (ctx.get("resume") or {}).get("extracted_text_preview")
    resume = resume or "No resume text available. Please upload your resume first via the Resume page."

    # Extract target from context
    ctx = state.get("student_context") or {}
    companies = (ctx.get("profile") or {}).get("preferred_companies") or []
    domains = (ctx.get("profile") or {}).get("preferred_domains") or []
    auto_target_company = target_company or (companies[0] if companies else "top product companies")
    auto_target_role = target_role or (domains[0] if domains else "Software Engineer")

    prompt = ChatPromptTemplate.from_messages([
        ("system", RESUME_REVIEW_SYSTEM),
        ("human", RESUME_REVIEW_USER),
    ])

    chain = prompt | llm | JsonOutputParser()

    try:
        result = await chain.ainvoke({
            "student_context": student_ctx,
            "resume_text": resume,
            "target_role": auto_target_role,
            "target_company": auto_target_company,
        })

        logger.info(f"[ResumeReview] ATS Score: {result.get('ats_score')}")

        response = (
            f"📄 **Resume Review Complete**\n\n"
            f"**ATS Score**: {result.get('ats_score', 'N/A')}/100\n"
            f"**Overall Score**: {result.get('overall_score', 'N/A')}/10\n\n"
            f"**Summary**: {result.get('summary', '')}\n\n"
            f"**Strengths**:\n" + "\n".join(f"✅ {s}" for s in result.get("strengths", [])) + "\n\n"
            f"**Areas to Improve**:\n" + "\n".join(f"⚠️ {w}" for w in result.get("weaknesses", [])) + "\n\n"
            f"**Top Suggestions**:\n" + "\n".join(
                f"🔧 [{s['priority'].upper()}] {s['issue']} → {s['fix']}"
                for s in sorted(result.get("suggestions", []), key=lambda x: {"high": 0, "medium": 1, "low": 2}.get(x.get("priority", "low"), 2))[:5]
            )
        )

        return {
            **state,
            "resume_review": result,
            "final_response": response,
            "suggested_next_action": "Based on these suggestions, would you like me to identify your skill gaps or generate a preparation roadmap?",
        }

    except Exception as e:
        logger.error(f"[ResumeReview] Failed: {e}")
        return {
            **state,
            "error": f"Resume review failed: {str(e)}",
            "final_response": "I encountered an issue reviewing your resume. Please try again.",
        }
