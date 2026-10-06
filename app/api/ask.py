"""
POST /ask endpoint implementation.
Follows the exact contract defined in Section 19.
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Header, HTTPException, Request
from pydantic import BaseModel, Field
from app.agent.graph import run_agent
from app.security.validation import validate_question_text

router = APIRouter(tags=["Student Services Assistant"])


class AskRequest(BaseModel):
    question: str = Field(..., description="Student's query about policies, attendance, marks, or eligibility")
    as_of_date: Optional[str] = Field("2026-10-06", description="Effective date for evaluation (YYYY-MM-DD)")


class AskResponse(BaseModel):
    trace_id: str
    answer_type: str
    answer: str
    citations: List[Dict[str, Any]] = []
    tools_invoked: List[str] = []
    applied_rules: List[Dict[str, Any]] = []
    conflicts_detected: List[str] = []
    policy_notes: List[str] = []
    audit_id: str
    latency_ms: float = 0.0


@router.post("/ask", response_model=AskResponse)
async def ask_question(
    req: AskRequest,
    x_student_id: Optional[str] = Header(None, alias="X-Student-Id")
):
    if not x_student_id or not x_student_id.strip():
        raise HTTPException(
            status_code=400,
            detail="Missing required header 'X-Student-Id'. Please provide a valid student identifier."
        )

    is_valid, err_msg = validate_question_text(req.question)
    if not is_valid:
        raise HTTPException(status_code=422, detail=err_msg)

    # Execute LangGraph pipeline
    result_state = run_agent(
        question=req.question,
        student_id=x_student_id,
        as_of_date=req.as_of_date or "2026-10-06"
    )

    return AskResponse(
        trace_id=result_state["trace_id"],
        answer_type=result_state["answer_type"],
        answer=result_state["answer"],
        citations=result_state.get("citations", []),
        tools_invoked=result_state.get("tools_invoked", []),
        applied_rules=result_state.get("rules_applied", []),
        conflicts_detected=result_state.get("conflicts_detected", []),
        policy_notes=result_state.get("policy_notes", []),
        audit_id=result_state["audit_id"],
        latency_ms=result_state.get("latency_ms", 0.0)
    )
