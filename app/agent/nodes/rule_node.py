"""
Rule evaluation node for LangGraph pipeline.
Evaluates deterministic regulatory thresholds and attaches official citations.
"""

from typing import Any, Dict
from app.agent.state import AgentState
from app.services.citation import deduplicate_citations
from app.tools.eligibility import check_exam_eligibility


def evaluate_rules_node(state: AgentState) -> Dict[str, Any]:
    if state.get("answer_type") in ["refused", "clarification_needed"]:
        return {}

    intent = state.get("intent")
    student_id = state["student_id"]
    course_code = state.get("course_code")
    exam_type = state.get("exam_type", "REGULAR")

    rules_applied = list(state.get("rules_applied", []))
    citations = list(state.get("citations", []))

    if intent == "eligibility_check" and course_code:
        elig_res = check_exam_eligibility(
            student_id=student_id,
            course_code=course_code,
            exam_type=exam_type,
            as_of_date=state.get("as_of_date", "2026-10-06")
        )

        state["tool_outputs"].append({"tool": "check_exam_eligibility", "output": elig_res})
        rules_applied.extend(elig_res.get("rules_applied", []))

        # Add citations for the rules applied
        for src in elig_res.get("sources", []):
            citations.append({
                "title": "Official Examination & Academic Regulations",
                "doc_id": src.get("doc_id", "ACAD-REG-2024"),
                "section": src.get("section", "Section 4.1"),
                "page": 1,
                "version": "3.1",
                "effective_date": "2024-07-01",
                "authority_level": 1
            })

    return {
        "rules_applied": rules_applied,
        "citations": deduplicate_citations(citations)
    }
