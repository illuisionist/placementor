"""
Mock Interview Agent — conducts simulated interviews and evaluates answers.

Supports: HR, Technical, DSA, Core CS, Behavioral
Each session is stateful — multiple Q&A turns per interview.
"""

import json
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
from agents.state import AgentState
from agents.llm_factory import get_groq_llm
from loguru import logger

# ─── Interview Starter ────────────────────────────────────────────────────────

START_SYSTEM = """You are an experienced interviewer from {company} conducting a {interview_type} interview.

Student background:
{student_context}

Interview focus areas: {focus_areas}

Rules:
- Ask ONE question at a time.
- Start with a warm intro then your first question.
- Questions should be appropriate for the student's level (CGPA: {cgpa}).
- Be professional and encouraging but realistic.
- For DSA questions, describe the problem clearly with examples.

Begin the interview with a brief introduction and your first question."""

# ─── Answer Evaluator ─────────────────────────────────────────────────────────

EVALUATE_SYSTEM = """You are evaluating a student's interview answer.

Question asked: {question}
Student's answer: {student_answer}
Interview type: {interview_type}
Student level: CGPA {cgpa}

Evaluate and respond with valid JSON:
{{
    "score": <0-10>,
    "is_correct": true/false,
    "strengths": ["<what was good>"],
    "weaknesses": ["<what was missing/wrong>"],
    "ideal_answer_points": ["<key point 1>", "<key point 2>"],
    "next_question": "<your next interview question>",
    "is_interview_complete": false,
    "encouragement": "<short encouraging remark>"
}}

After 8-10 questions, set is_interview_complete to true and provide no next_question."""

# ─── Final Evaluation ─────────────────────────────────────────────────────────

FINAL_EVAL_SYSTEM = """You are providing the final evaluation of a mock interview session.

Interview transcript:
{transcript}

Interview type: {interview_type}
Company: {company}

Provide a comprehensive evaluation in valid JSON:
{{
    "overall_score": <0-10>,
    "technical_score": <0-10>,
    "communication_score": <0-10>,
    "confidence_score": <0-10>,
    "strengths": ["<strength1>", "<strength2>"],
    "weaknesses": ["<weakness1>", "<weakness2>"],
    "topic_wise_performance": {{
        "<topic>": <score 0-10>
    }},
    "improvement_suggestions": ["<suggestion1>", "<suggestion2>"],
    "recommended_resources": [
        {{"topic": "<topic>", "resource": "<resource name/URL>", "why": "<why this helps>"}}
    ],
    "readiness_for_company": <0-100>,
    "next_interview_focus": "<what to focus on in next mock interview>",
    "motivational_message": "<personalized encouraging message>"
}}"""


async def mock_interview_agent(state: AgentState, action: str = "start",
                                interview_type: str = "technical",
                                target_company: str = "",
                                student_answer: str = "") -> AgentState:
    """
    LangGraph node: Mock Interview Agent.
    
    action: 'start' | 'answer' | 'evaluate'
    """
    llm = get_groq_llm(temperature=0.7)  # Slightly higher temp for variety
    student_ctx = state.get("student_context") or {}
    cgpa = student_ctx.get("profile", {}).get("cgpa", 7.0)
    interview_state = state.get("_interview_state") or {}

    if not target_company:
        companies = student_ctx.get("profile", {}).get("preferred_companies", [])
        target_company = companies[0] if companies else "a top tech company"

    FOCUS_AREAS = {
        "technical": ["Data Structures", "Algorithms", "System Design basics", "OOP", "DBMS"],
        "dsa": ["Arrays", "Linked Lists", "Trees", "Graphs", "Dynamic Programming"],
        "hr": ["Introduction", "Strengths & Weaknesses", "Why this company", "Situational questions"],
        "core_cs": ["OS", "DBMS", "Computer Networks", "OOP"],
        "behavioral": ["STAR method questions", "Leadership", "Teamwork", "Conflict resolution"],
    }

    focus = FOCUS_AREAS.get(interview_type, FOCUS_AREAS["technical"])

    if action == "start":
        prompt = ChatPromptTemplate.from_messages([
            ("system", START_SYSTEM),
            ("human", "Please begin the interview."),
        ])
        chain = prompt | llm | StrOutputParser()

        response = await chain.ainvoke({
            "company": target_company,
            "interview_type": interview_type.upper(),
            "student_context": json.dumps(student_ctx, indent=2),
            "focus_areas": ", ".join(focus),
            "cgpa": cgpa,
        })

        new_interview_state = {
            "type": interview_type,
            "company": target_company,
            "transcript": [],
            "question_count": 0,
            "scores": [],
            "current_question": response,
            "status": "in_progress",
        }

        return {
            **state,
            "_interview_state": new_interview_state,
            "final_response": response,
            "suggested_next_action": "Type your answer to proceed. Type 'end interview' to finish early.",
        }

    elif action == "answer":
        current_q = interview_state.get("current_question", "")
        transcript = interview_state.get("transcript", [])
        q_count = interview_state.get("question_count", 0)

        # Evaluate the answer
        prompt = ChatPromptTemplate.from_messages([
            ("system", EVALUATE_SYSTEM),
            ("human", "Evaluate this answer and provide the next question."),
        ])
        chain = prompt | llm | JsonOutputParser()

        result = await chain.ainvoke({
            "question": current_q,
            "student_answer": student_answer,
            "interview_type": interview_type,
            "cgpa": cgpa,
        })

        # Update transcript
        transcript.append({
            "question": current_q,
            "answer": student_answer,
            "score": result.get("score"),
            "feedback": result.get("weaknesses", []),
            "ideal_points": result.get("ideal_answer_points", []),
        })

        interview_state["transcript"] = transcript
        interview_state["scores"].append(result.get("score", 5))
        interview_state["question_count"] = q_count + 1

        if result.get("is_interview_complete") or q_count >= 9:
            # Trigger final evaluation
            return await mock_interview_agent(
                {**state, "_interview_state": interview_state},
                action="evaluate",
                interview_type=interview_type,
                target_company=target_company,
            )

        # Continue with next question
        next_q = result.get("next_question", "")
        interview_state["current_question"] = next_q

        response = (
            f"**Feedback on your answer:**\n"
            f"Score: {result.get('score', 'N/A')}/10\n"
            f"{result.get('encouragement', '')}\n\n"
        )
        if result.get("weaknesses"):
            response += "**What to improve**: " + "; ".join(result["weaknesses"][:2]) + "\n\n"

        response += f"**Next Question:**\n{next_q}"

        return {
            **state,
            "_interview_state": interview_state,
            "final_response": response,
        }

    elif action == "evaluate":
        transcript = interview_state.get("transcript", [])
        transcript_str = json.dumps(transcript, indent=2)

        prompt = ChatPromptTemplate.from_messages([
            ("system", FINAL_EVAL_SYSTEM),
            ("human", "Provide the final interview evaluation."),
        ])
        chain = prompt | llm | JsonOutputParser()

        result = await chain.ainvoke({
            "transcript": transcript_str,
            "interview_type": interview_type,
            "company": target_company,
        })

        logger.info(f"[MockInterview] Final score: {result.get('overall_score')}/10")

        response = (
            f"🎉 **Interview Complete — Final Evaluation**\n\n"
            f"**Overall Score**: {result.get('overall_score', 'N/A')}/10\n"
            f"**Technical**: {result.get('technical_score', 'N/A')}/10 | "
            f"**Communication**: {result.get('communication_score', 'N/A')}/10\n"
            f"**Company Readiness**: {result.get('readiness_for_company', 'N/A')}%\n\n"
            f"**Strengths**:\n" + "\n".join(f"✅ {s}" for s in result.get("strengths", [])) + "\n\n"
            f"**Areas to Improve**:\n" + "\n".join(f"⚠️ {w}" for w in result.get("weaknesses", [])) + "\n\n"
            f"**Recommended Resources**:\n" + "\n".join(
                f"📖 {r['topic']}: {r['resource']}" for r in result.get("recommended_resources", [])[:3]
            ) + "\n\n"
            f"💬 {result.get('motivational_message', '')}\n\n"
            f"**Next Focus**: {result.get('next_interview_focus', '')}"
        )

        return {
            **state,
            "interview_result": result,
            "_interview_state": {**interview_state, "status": "completed"},
            "final_response": response,
            "suggested_next_action": "Would you like me to update your roadmap based on this interview performance?",
        }

    return state
