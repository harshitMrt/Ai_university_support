"""
Tool selection and execution nodes for LangGraph pipeline.
Invokes deterministic student records, attendance, results, and course lookups.
"""

from typing import Any, Dict
from app.agent.state import AgentState
from app.tools.student import get_student
from app.tools.attendance import get_attendance
from app.tools.results import get_result
from app.tools.policy import get_course


def select_tool_node(state: AgentState) -> Dict[str, Any]:
    if state.get("answer_type") in ["refused", "clarification_needed"]:
        return {}

    intent = state.get("intent")
    tools = []

    if intent in ["eligibility_check", "student_personal"]:
        tools.append("get_student")
        if state.get("course_code"):
            tools.append("get_attendance")
            tools.append("get_result")
            tools.append("get_course")
        else:
            tools.append("get_attendance")

    if intent == "eligibility_check":
        tools.append("check_exam_eligibility")

    return {"tools_invoked": tools}


def execute_tool_node(state: AgentState) -> Dict[str, Any]:
    if state.get("answer_type") in ["refused", "clarification_needed"]:
        return {}

    tools = state.get("tools_invoked", [])
    student_id = state["student_id"]
    course_code = state.get("course_code")

    tool_inputs = []
    tool_outputs = []

    for t in tools:
        if t == "get_student":
            tool_inputs.append({"tool": "get_student", "student_id": student_id})
            res = get_student(student_id)
            tool_outputs.append({"tool": "get_student", "output": res})

        elif t == "get_attendance":
            tool_inputs.append({"tool": "get_attendance", "student_id": student_id, "course_code": course_code})
            res = get_attendance(student_id, course_code)
            tool_outputs.append({"tool": "get_attendance", "output": res})

        elif t == "get_result":
            if course_code:
                tool_inputs.append({"tool": "get_result", "student_id": student_id, "course_code": course_code})
                res = get_result(student_id, course_code)
                tool_outputs.append({"tool": "get_result", "output": res})

        elif t == "get_course":
            if course_code:
                tool_inputs.append({"tool": "get_course", "course_code": course_code})
                res = get_course(course_code)
                tool_outputs.append({"tool": "get_course", "output": res})

    return {
        "tool_inputs": tool_inputs,
        "tool_outputs": tool_outputs
    }
