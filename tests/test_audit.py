"""
Unit tests for Audit and Traceability.
"""

import uuid
from fastapi.testclient import TestClient
from app.main import app
from app.audit.logger import record_audit, get_audit_record

client = TestClient(app)


def test_audit_record_and_retrieve():
    trace_id = str(uuid.uuid4())
    record_audit(
        trace_id=trace_id,
        student_id="S1001",
        question="What is my attendance?",
        answer_type="calculated",
        final_answer="75.0%",
        latency_ms=12.5,
        model_used="test-model",
        selected_sources=[{"doc_id": "ACAD-REG-2024"}],
        tools_invoked=["get_attendance"]
    )

    rec = get_audit_record(trace_id)
    assert rec is not None
    assert rec["trace_id"] == trace_id
    assert rec["student_id"] == "S1001"
    assert rec["answer_type"] == "calculated"
    assert "get_attendance" in rec["tools_invoked"]

    # Test via API
    resp = client.get(f"/audit/{trace_id}")
    assert resp.status_code == 200
    assert resp.json()["trace_id"] == trace_id


def test_audit_list_endpoint():
    resp = client.get("/audit?limit=10")
    assert resp.status_code == 200
    assert "records" in resp.json()
    assert resp.json()["count"] >= 1
