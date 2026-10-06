"""
Intent classification node for LangGraph pipeline.
Inspects privacy boundaries, prompt injection attempts, course code extraction,
and intent categorization.
"""

import re
from typing import Any, Dict
from app.agent.state import AgentState
from app.core.security import inspect_privacy_boundaries, inspect_prompt_injection
from app.tools.student import get_student

COURSE_CODE_REGEX = re.compile(r"\b(CS\d{3}|EC\d{3}|MA\d{3}|JDG\d{3})\b", re.IGNORECASE)
SUPP_KEYWORDS = ["supplementary", "supp", "backlog exam", "failed", "re-appear", "reappear"]

COURSE_NAME_MAP = {
    "data structures": "CS201",
    "dsa": "CS201",
    "database": "CS202",
    "dbms": "CS202",
    "operating system": "CS203",
    "signal processing": "EC201",
    "dsp": "EC201",
    "microprocessor": "EC202",
    "discrete math": "MA201",
}


def classify_intent_node(state: AgentState) -> Dict[str, Any]:
    question = state["question"]
    student_id = state["student_id"]

    # 1. Privacy inspection
    is_violation, refusal_reason = inspect_privacy_boundaries(question, student_id)
    if is_violation:
        return {
            "intent": "privacy_violation",
            "answer_type": "refused",
            "answer": refusal_reason or "Personal student information cannot be disclosed."
        }

    # 2. Prompt injection inspection
    is_injection, injection_reason = inspect_prompt_injection(question)
    if is_injection:
        return {
            "intent": "prompt_injection",
            "answer_type": "refused",
            "answer": injection_reason
        }

    # 3. Detect course code
    course_match = COURSE_CODE_REGEX.search(question)
    course_code = course_match.group(1).upper() if course_match else None

    q_lower = question.lower()
    if not course_code:
        for name_keyword, mapped_code in COURSE_NAME_MAP.items():
            if name_keyword in q_lower:
                course_code = mapped_code
                break

    # 4. Detect exam type
    is_supp = any(k in q_lower for k in SUPP_KEYWORDS)
    exam_type = "SUPPLEMENTARY" if is_supp else "REGULAR"

    # 5. Fetch student profile
    student_rec = get_student(student_id)

    # 6. Check for missing context (clarification needed)
    if q_lower.strip().rstrip("?") in ["can i apply", "am i eligible", "what is my status"] and not course_code:
        return {
            "intent": "clarification_needed",
            "answer_type": "clarification_needed",
            "answer": "Could you please specify which course or examination you are inquiring about (e.g., end-semester exam in CS201 or supplementary exam)?",
            "student_record": student_rec,
            "course_code": None,
            "exam_type": exam_type,
        }

    # Personal student queries
    personal_indicators = [
        "my attendance", "overall attendance", "attendance percentage", "classes attended",
        "how many classes", "my marks", "my result", "did i pass", "am i eligible",
        "can i take", "can i appear", "my backlogs", "my cgpa", "why am i not eligible",
        "my current attendance", "all courses"
    ]

    is_personal = any(ind in q_lower for ind in personal_indicators) or (
        "my" in q_lower and ("attendance" in q_lower or "marks" in q_lower or "grades" in q_lower or "results" in q_lower)
    )
    is_eligibility = "eligible" in q_lower or "can i" in q_lower or "permitted" in q_lower

    if is_eligibility and (course_code or "exam" in q_lower or "supp" in q_lower):
        intent = "eligibility_check"
    elif is_personal:
        intent = "student_personal"
    else:
        intent = "policy_factual"

    return {
        "intent": intent,
        "course_code": course_code,
        "exam_type": exam_type,
        "student_record": student_rec,
    }
