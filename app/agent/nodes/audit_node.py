"""
Audit recording node for LangGraph pipeline.
Calculates end-to-end execution latency and records immutable audit log.
"""

import time
import uuid
from typing import Any, Dict
from app.agent.state import AgentState
from app.core.config import settings
from app.repositories.audit_repository import AuditRepository


def create_audit_record_node(state: AgentState) -> Dict[str, Any]:
    start_time = state.get("start_time", time.time())
    latency_ms = round((time.time() - start_time) * 1000.0, 2)
    trace_id = state.get("trace_id", str(uuid.uuid4()))

    AuditRepository.record_audit(
        trace_id=trace_id,
        student_id=state.get("student_id", "UNKNOWN"),
        question=state.get("question", ""),
        answer_type=state.get("answer_type", "not_found"),
        final_answer=state.get("answer", ""),
        latency_ms=latency_ms,
        model_used=state.get("model_used", settings.OLLAMA_MODEL),
        selected_sources=[state.get("selected_source")] if state.get("selected_source") else [],
        retrieved_sources=[c.get("metadata") for c in state.get("retrieved_chunks", [])],
        tools_invoked=state.get("tools_invoked", []),
        tool_inputs=state.get("tool_inputs", []),
        tool_outputs=state.get("tool_outputs", []),
        rules_applied=state.get("rules_applied", []),
        conflicts_detected=state.get("conflicts_detected", [])
    )

    return {
        "trace_id": trace_id,
        "audit_id": trace_id,
        "latency_ms": latency_ms
    }
