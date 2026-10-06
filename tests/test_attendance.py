"""
Unit tests for Deterministic Attendance Tool.
"""

from app.tools.attendance import get_attendance


def test_attendance_exact_threshold():
    # S1001 in CS201: 30 / 40 = 75.0%
    res = get_attendance("S1001", "CS201")
    assert isinstance(res, dict)
    assert res["found"] is True
    assert res["classes_held"] == 40
    assert res["classes_attended"] == 30
    assert res["attendance_percentage"] == 75.0
    assert res["status"] == "Satisfactory"


def test_attendance_below_threshold():
    # S1002 in CS201: 29 / 40 = 72.5%
    res = get_attendance("S1002", "CS201")
    assert isinstance(res, dict)
    assert res["found"] is True
    assert res["classes_held"] == 40
    assert res["classes_attended"] == 29
    assert res["attendance_percentage"] == 72.5
    assert res["status"] == "Shortage"


def test_attendance_above_threshold():
    # S1003 in CS201: 34 / 40 = 85.0%
    res = get_attendance("S1003", "CS201")
    assert isinstance(res, dict)
    assert res["found"] is True
    assert res["attendance_percentage"] == 85.0
    assert res["status"] == "Satisfactory"


def test_attendance_aggregate_all_courses():
    res = get_attendance("S1001")
    assert isinstance(res, dict)
    assert res["found"] is True
    assert "courses" in res
    assert len(res["courses"]) >= 2
    assert "overall_attendance_percentage" in res
