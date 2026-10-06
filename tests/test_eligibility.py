"""
Unit tests for Deterministic Eligibility Calculation Engine.
"""

from app.tools.eligibility import check_exam_eligibility


def test_regular_exam_eligible_exact_75():
    res = check_exam_eligibility("S1001", "CS201", exam_type="REGULAR")
    assert res["eligible"] is True
    assert res["attendance_percentage"] == 75.0
    assert any(r["rule_id"] == "ATT-MIN-01" and r["passed"] for r in res["rules_applied"])


def test_regular_exam_ineligible_below_75():
    res = check_exam_eligibility("S1002", "CS201", exam_type="REGULAR")
    assert res["eligible"] is False
    assert res["attendance_percentage"] == 72.5
    assert any(r["rule_id"] == "ATT-MIN-01" and not r["passed"] for r in res["rules_applied"])


def test_supplementary_eligible():
    # S1005: failed CS201, attendance 80.0%, backlogs=1
    res = check_exam_eligibility("S1005", "CS201", exam_type="SUPPLEMENTARY")
    assert res["eligible"] is True
    assert res["attendance_percentage"] == 80.0
    assert res["active_backlogs"] == 1


def test_supplementary_ineligible_attendance():
    # S1006: failed CS201, but attendance 70.0% < 75.0%
    res = check_exam_eligibility("S1006", "CS201", exam_type="SUPPLEMENTARY")
    assert res["eligible"] is False
    assert "Attendance of 70.0% is below" in res["reason"]


def test_supplementary_ineligible_excess_backlogs():
    # S1007: active_backlogs = 3 (> 2)
    res = check_exam_eligibility("S1007", "CS201", exam_type="SUPPLEMENTARY")
    assert res["eligible"] is False
    assert "exceeds the maximum permissible limit" in res["reason"]
