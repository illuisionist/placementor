"""
Roadmap Agent — generates a personalized weekly preparation plan.

Takes the student's profile, skill gaps, target company, and available
time to produce a structured, week-by-week roadmap.
"""

import json
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from agents.state import AgentState
from agents.llm_factory import get_groq_llm
from loguru import logger

ROADMAP_SYSTEM = """You are the Roadmap Agent for PlaceMentor AI.

Create a personalized, realistic, and detailed placement preparation roadmap.

Guidelines:
- Be specific about daily/weekly tasks, not vague suggestions.
- Prioritize critical skill gaps first.
- Balance: DSA (40%), Core CS (25%), Projects (20%), Aptitude (10%), Soft Skills (5%)
- Include specific LeetCode problem categories AND provide actual URL links to LeetCode patterns or problems.
- Suggest actual URL links for free resources (YouTube video links, Medium articles, GeeksforGeeks, NeetCode, etc.) for every topic.
- Include an actionable checklist of concrete tasks to accomplish the weekly goals.
- Include checkpoints for mock interviews (every 2 weeks)
- Adjust difficulty based on CGPA and current skill level

Student Profile:
{student_context}

Skill Gaps Identified:
{skill_gaps}

Available preparation time: {weeks_available} weeks
Target company: {target_company}
Target role: {target_role}

Respond ONLY with valid JSON:
{{
    "title": "<roadmap title>",
    "target_company": "<company>",
    "target_role": "<role>",
    "duration_weeks": <number>,
    "weekly_hours_required": <hours per week>,
    "weeks": [
        {{
            "week": 1,
            "theme": "<week theme>",
            "goals": ["<goal1>", "<goal2>"],
            "checklist": [
                {{"task": "<concrete actionable task>", "is_completed": false}}
            ],
            "dsa": {{
                "topics": ["<topic1>"],
                "problems_target": <number>,
                "problem_types": ["Easy", "Medium"],
                "resources": [
                    {{"title": "<title>", "url": "<URL to leetcode/youtube/article>"}}
                ]
            }},
            "core_subjects": [
                {{"subject": "<subject>", "topics": ["<topic>"], "resource_title": "<name>", "resource_url": "<URL to youtube/article>"}}
            ],
            "projects": "<project task or null>",
            "aptitude": "<aptitude focus area>",
            "resume": "<resume update task or null>",
            "mock_interview": false,
            "checkpoint": "<what to evaluate at end of week>"
        }}
    ],
    "milestones": [
        {{"week": <n>, "milestone": "<what should be achieved"}}
    ],
    "resources": {{
        "dsa": [{{"title": "<title>", "url": "<url>"}}],
        "system_design": [{{"title": "<title>", "url": "<url>"}}],
        "aptitude": [{{"title": "<title>", "url": "<url>"}}],
        "core_cs": [{{"title": "<title>", "url": "<url>"}}]
    }},
    "daily_schedule_template": {{
        "weekday_hours": <hours>,
        "weekend_hours": <hours>,
        "morning": "<what to do in morning>",
        "evening": "<what to do in evening>"
    }}
}}"""

ROADMAP_USER = "Generate a personalized roadmap for the student."


async def roadmap_agent(state: AgentState, weeks_available: int = 8,
                         target_company: str = "", target_role: str = "") -> AgentState:
    """LangGraph node: Roadmap Agent."""
    llm = get_groq_llm()

    student_ctx = json.dumps(state.get("student_context") or {}, indent=2)
    skill_gaps = json.dumps(state.get("skill_gap") or {}, indent=2)

    if not target_company:
        prefs = (state.get("student_context") or {}).get("profile", {})
        companies = prefs.get("preferred_companies", [])
        target_company = companies[0] if companies else "top product companies"

    if not target_role:
        domains = (state.get("student_context") or {}).get("profile", {}).get("preferred_domains", [])
        target_role = domains[0] if domains else "Software Development Engineer"

    prompt = ChatPromptTemplate.from_messages([
        ("system", ROADMAP_SYSTEM),
        ("human", ROADMAP_USER),
    ])

    chain = prompt | llm | JsonOutputParser()

    try:
        result = await chain.ainvoke({
            "student_context": student_ctx,
            "skill_gaps": skill_gaps,
            "weeks_available": weeks_available,
            "target_company": target_company,
            "target_role": target_role,
        })

        logger.info(f"[Roadmap] Generated {result.get('duration_weeks')} week roadmap for {target_company}")

        # Format a readable summary (first 3 weeks shown)
        weeks = result.get("weeks", [])
        week_summaries = []
        for w in weeks[:3]:
            dsa_info = w.get("dsa", {})
            checklist_items = w.get("checklist", [])
            checklist_preview = f"✅ Tasks: {len(checklist_items)} action items\n" if checklist_items else ""
            week_summaries.append(
                f"**Week {w['week']}: {w.get('theme', '')}**\n"
                f"🎯 Goals: {', '.join(w.get('goals', []))}\n"
                f"💻 DSA: {', '.join(dsa_info.get('topics', []))} ({dsa_info.get('problems_target', 0)} problems)\n"
                f"📚 Core: {', '.join(cs.get('subject', '') for cs in w.get('core_subjects', []))}\n"
                + checklist_preview +
                f"📌 Checkpoint: {w.get('checkpoint', '')}"
            )

        def format_resource(r):
            if isinstance(r, dict):
                return f"[{r.get('title', 'Link')}]({r.get('url', '#')})"
            return str(r)

        response = (
            f"🗺️ **Your Personalized Roadmap — {target_company} ({target_role})**\n\n"
            f"📅 Duration: **{result.get('duration_weeks')} weeks** | "
            f"⏰ ~{result.get('weekly_hours_required', 'N/A')} hrs/week\n\n"
            f"**Preview (First 3 Weeks)**:\n\n"
            + "\n\n".join(week_summaries)
            + f"\n\n...and {max(0, len(weeks)-3)} more weeks planned.\n\n"
            f"**Key Resources**:\n"
            + "\n".join(f"• {format_resource(r)}" for r in result.get("resources", {}).get("dsa", [])[:3])
            + "\n\n💡 I've saved your full roadmap. Check the Roadmap section for the complete plan."
        )

        return {
            **state,
            "roadmap": result,
            "final_response": response,
            "suggested_next_action": "Would you like to start a mock interview to assess your current level, or shall we begin with Week 1 resources?",
        }

    except Exception as e:
        logger.error(f"[Roadmap] Failed: {e}")
        return {
            **state,
            "error": f"Roadmap generation failed: {str(e)}",
            "final_response": "I couldn't generate your roadmap right now. Please try again.",
        }
