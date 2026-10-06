"""
Unit tests for FastAPI endpoints.
"""

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_endpoint():
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert "status" in data
    assert data["api"] is True
    assert data["database"] is True
    assert data["chromadb"] is True


def test_sources_endpoint():
    resp = client.get("/sources")
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] >= 10
    assert any(s["doc_id"] == "ACAD-REG-2024" for s in data["sources"])


def test_student_endpoint():
    resp = client.get("/student/S1001")
    assert resp.status_code == 200
    data = resp.json()
    assert data["student"]["student_id"] == "S1001"
    assert "attendance" in data


def test_ask_missing_header():
    resp = client.post("/ask", json={"question": "What is my attendance in CS201?"})
    assert resp.status_code == 400
    assert "Missing required header" in resp.json()["detail"]


def test_ask_valid_query():
    resp = client.post(
        "/ask",
        headers={"X-Student-Id": "S1001"},
        json={"question": "What is my attendance in CS201?"}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["answer_type"] == "calculated"
    assert "trace_id" in data
    assert "75.0%" in data["answer"]
