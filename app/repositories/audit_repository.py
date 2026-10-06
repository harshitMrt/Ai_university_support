"""
Repository for persisting and querying execution audit trails in SQLite audit_log table.
"""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional
from app.database.connection import get_connection


class AuditRepository:
    @staticmethod
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
        conn = get_connection()
        try:
            cursor = conn.cursor()
            timestamp = datetime.now().isoformat()
            cursor.execute(
                """
                INSERT OR REPLACE INTO audit_log (
                    trace_id, timestamp, student_id, question, answer_type,
                    selected_sources, retrieved_sources, tools_invoked,
                    tool_inputs, tool_outputs, rules_applied,
                    conflicts_detected, model_used, latency_ms, final_answer
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    trace_id,
                    timestamp,
                    student_id,
                    question,
                    answer_type,
                    json.dumps(selected_sources or []),
                    json.dumps(retrieved_sources or []),
                    json.dumps(tools_invoked or []),
                    json.dumps(tool_inputs or []),
                    json.dumps(tool_outputs or []),
                    json.dumps(rules_applied or []),
                    json.dumps(conflicts_detected or []),
                    model_used,
                    latency_ms,
                    final_answer
                )
            )
            conn.commit()
        finally:
            conn.close()

    @staticmethod
    def get_by_trace_id(trace_id: str) -> Optional[Dict[str, Any]]:
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT trace_id, timestamp, student_id, question, answer_type,
                       selected_sources, retrieved_sources, tools_invoked,
                       tool_inputs, tool_outputs, rules_applied,
                       conflicts_detected, model_used, latency_ms, final_answer
                FROM audit_log
                WHERE trace_id = ?
                """,
                (trace_id.strip(),)
            )
            row = cursor.fetchone()
            if not row:
                return None
            return {
                "trace_id": row["trace_id"],
                "timestamp": row["timestamp"],
                "student_id": row["student_id"],
                "question": row["question"],
                "answer_type": row["answer_type"],
                "selected_sources": json.loads(row["selected_sources"] or "[]"),
                "retrieved_sources": json.loads(row["retrieved_sources"] or "[]"),
                "tools_invoked": json.loads(row["tools_invoked"] or "[]"),
                "tool_inputs": json.loads(row["tool_inputs"] or "[]"),
                "tool_outputs": json.loads(row["tool_outputs"] or "[]"),
                "rules_applied": json.loads(row["rules_applied"] or "[]"),
                "conflicts_detected": json.loads(row["conflicts_detected"] or "[]"),
                "model_used": row["model_used"],
                "latency_ms": float(row["latency_ms"] or 0.0),
                "final_answer": row["final_answer"],
            }
        finally:
            conn.close()

    @staticmethod
    def list_recent(limit: int = 50) -> List[Dict[str, Any]]:
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT trace_id, timestamp, student_id, question, answer_type,
                       selected_sources, tools_invoked, latency_ms, final_answer
                FROM audit_log
                ORDER BY timestamp DESC
                LIMIT ?
                """,
                (limit,)
            )
            rows = cursor.fetchall()
            return [
                {
                    "trace_id": r["trace_id"],
                    "timestamp": r["timestamp"],
                    "student_id": r["student_id"],
                    "question": r["question"],
                    "answer_type": r["answer_type"],
                    "selected_sources": json.loads(r["selected_sources"] or "[]"),
                    "tools_invoked": json.loads(r["tools_invoked"] or "[]"),
                    "latency_ms": float(r["latency_ms"] or 0.0),
                    "final_answer": r["final_answer"],
                }
                for r in rows
            ]
        finally:
            conn.close()
