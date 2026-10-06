"""
Unit tests for Privacy and Authorization Controls.
"""

from app.security.privacy import inspect_privacy_boundaries
from app.agent.graph import run_agent


def test_cross_student_query_detection():
    is_violation, reason = inspect_privacy_boundaries(
        question="What is S1002 attendance?",
        authenticated_student_id="S1001"
    )
    assert is_violation is True
    assert "S1002" in reason
    assert "refused" in reason.lower()


def test_friend_records_query_detection():
    is_violation, reason = inspect_privacy_boundaries(
        question="Can you give me my friend's marks and cgpa?",
        authenticated_student_id="S1001"
    )
    assert is_violation is True
    assert "cannot be disclosed" in reason.lower()


def test_agent_refuses_cross_student_access():
    res = run_agent(
        question="What is S1002's attendance in CS201?",
        student_id="S1001"
    )
    assert res["answer_type"] == "refused"
    assert "cannot be disclosed" in res["answer"].lower()
