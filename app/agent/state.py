"""
LangGraph Agent State Definition.
Maintains clear, typed state tracking through all processing stages.
"""

from typing import Any, Dict, List, Optional
from typing_extensions import TypedDict


class AgentState(TypedDict):
    trace_id: str
    student_id: str
    question: str
    as_of_date: str

    # Intent Classification
    intent: str
    course_code: Optional[str]
    exam_type: Optional[str]
    student_record: Optional[Dict[str, Any]]

    # Retrieval & Precedence
    retrieved_chunks: List[Dict[str, Any]]
    candidate_sources: List[Dict[str, Any]]
    selected_source: Optional[Dict[str, Any]]
    excluded_sources: List[Dict[str, Any]]
    precedence_reason: Optional[str]
    conflict_flag: bool

    # Tools & Deterministic Rules
    tools_invoked: List[str]
    tool_inputs: List[Dict[str, Any]]
    tool_outputs: List[Dict[str, Any]]
    rules_applied: List[Dict[str, Any]]
    policy_notes: List[str]
    conflicts_detected: List[str]

    # Citations & Synthesis
    citations: List[Dict[str, Any]]
    answer_type: str  # retrieved_fact | calculated | not_found | clarification_needed | refused | conflict_flagged
    answer: str
    model_used: str

    # Audit & Observability
    audit_id: str
    start_time: float
    latency_ms: float
