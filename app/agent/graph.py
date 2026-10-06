"""
LangGraph Orchestration Graph.
Connects the 9 processing nodes with conditional branching for early exits on security/clarification.
"""

import time
import uuid
from typing import Any, Dict, Optional
from langgraph.graph import StateGraph, START, END
from app.agent.state import AgentState
from app.agent.nodes import (
    classify_intent_node,
    retrieve_documents_node,
    source_resolution_node,
    select_tool_node,
    execute_tool_node,
    evaluate_rules_node,
    synthesize_answer_node,
    validate_grounding_node,
    create_audit_record_node,
)
from app.config import settings


def should_early_exit(state: AgentState) -> str:
    """
    Checks if classification flagged a refusal or missing information that terminates the pipeline early.
    """
    if state.get("answer_type") in ["refused", "clarification_needed"]:
        return "create_audit_record"
    return "retrieve_documents"


def build_student_services_graph():
    builder = StateGraph(AgentState)

    # 1. Add all 9 nodes
    builder.add_node("classify_intent", classify_intent_node)
    builder.add_node("retrieve_documents", retrieve_documents_node)
    builder.add_node("source_resolution", source_resolution_node)
    builder.add_node("select_tool", select_tool_node)
    builder.add_node("execute_tool", execute_tool_node)
    builder.add_node("evaluate_rules", evaluate_rules_node)
    builder.add_node("synthesize_answer", synthesize_answer_node)
    builder.add_node("validate_grounding", validate_grounding_node)
    builder.add_node("create_audit_record", create_audit_record_node)

    # 2. Add edges
    builder.add_edge(START, "classify_intent")

    builder.add_conditional_edges(
        "classify_intent",
        should_early_exit,
        {
            "create_audit_record": "create_audit_record",
            "retrieve_documents": "retrieve_documents"
        }
    )

    builder.add_edge("retrieve_documents", "source_resolution")
    builder.add_edge("source_resolution", "select_tool")
    builder.add_edge("select_tool", "execute_tool")
    builder.add_edge("execute_tool", "evaluate_rules")
    builder.add_edge("evaluate_rules", "synthesize_answer")
    builder.add_edge("synthesize_answer", "validate_grounding")
    builder.add_edge("validate_grounding", "create_audit_record")
    builder.add_edge("create_audit_record", END)

    return builder.compile()


_COMPILED_GRAPH = None


def get_agent_graph():
    global _COMPILED_GRAPH
    if _COMPILED_GRAPH is None:
        _COMPILED_GRAPH = build_student_services_graph()
    return _COMPILED_GRAPH


def run_agent(
    question: str,
    student_id: str,
    as_of_date: str = "2026-10-06",
    trace_id: str = None,
    top_k: Optional[int] = None
) -> Dict[str, Any]:
    """
    Executes the LangGraph pipeline synchronously for a user request.
    """
    graph = get_agent_graph()

    initial_state: AgentState = {
        "trace_id": trace_id or str(uuid.uuid4()),
        "student_id": student_id.strip() if student_id else "",
        "question": question.strip(),
        "as_of_date": as_of_date,
        "intent": "unknown",
        "course_code": None,
        "exam_type": None,
        "student_record": None,
        "top_k": top_k,
        "retrieved_chunks": [],
        "candidate_sources": [],
        "selected_source": None,
        "excluded_sources": [],
        "precedence_reason": None,
        "conflict_flag": False,
        "tools_invoked": [],
        "tool_inputs": [],
        "tool_outputs": [],
        "rules_applied": [],
        "policy_notes": [],
        "conflicts_detected": [],
        "citations": [],
        "answer_type": "not_found",
        "answer": "",
        "model_used": settings.OLLAMA_MODEL,
        "audit_id": "",
        "start_time": time.time(),
        "latency_ms": 0.0,
    }

    final_state = graph.invoke(initial_state)
    return final_state
