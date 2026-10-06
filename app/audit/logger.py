"""
Audit Logging and Traceability Module.
Persists execution metadata in the SQLite audit_log table.
Strictly records inputs, outputs, sources, tools, rules, and latency without logging chain-of-thought.
Delegates to app.repositories.audit_repository.
"""

from typing import Any, Dict, List, Optional
from app.repositories.audit_repository import AuditRepository


def record_audit(
    trace_id: str,
    student_id: str,
    question: str,
    answer_type: str,
    final_answer: str,
    latency_ms: float,
    model_used: str,
    selected_sources: Optional[List[Dict[str, Any]]] = None,
    retrieved_sources: Optional[List[Dict[str, Any]]] = None,
    tools_invoked: Optional[List[str]] = None,
    tool_inputs: Optional[List[Dict[str, Any]]] = None,
    tool_outputs: Optional[List[Dict[str, Any]]] = None,
    rules_applied: Optional[List[Dict[str, Any]]] = None,
    conflicts_detected: Optional[List[str]] = None
) -> None:
    AuditRepository.record_audit(
        trace_id=trace_id,
        student_id=student_id,
        question=question,
        answer_type=answer_type,
        final_answer=final_answer,
        latency_ms=latency_ms,
        model_used=model_used,
        selected_sources=selected_sources,
        retrieved_sources=retrieved_sources,
        tools_invoked=tools_invoked,
        tool_inputs=tool_inputs,
        tool_outputs=tool_outputs,
        rules_applied=rules_applied,
        conflicts_detected=conflicts_detected
    )


def get_audit_record(trace_id: str) -> Optional[Dict[str, Any]]:
    return AuditRepository.get_by_trace_id(trace_id)


def list_audit_records(limit: int = 50) -> List[Dict[str, Any]]:
    return AuditRepository.list_recent(limit=limit)
