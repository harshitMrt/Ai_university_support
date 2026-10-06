"""
Unit tests for data repository layer.
"""

from app.repositories.student_repository import StudentRepository
from app.repositories.attendance_repository import AttendanceRepository
from app.repositories.result_repository import ResultRepository
from app.repositories.rule_repository import RuleRepository
from app.repositories.audit_repository import AuditRepository


def test_student_repository_get_by_id():
    stu = StudentRepository.get_by_id("S1001")
    assert stu is not None
    assert stu["student_id"] == "S1001"
    assert "programme" in stu

    none_stu = StudentRepository.get_by_id("NONEXISTENT_9999")
    assert none_stu is None


def test_student_repository_get_course():
    course = StudentRepository.get_course_by_code("CS201")
    assert course is not None
    assert course["course_code"] == "CS201"

    none_course = StudentRepository.get_course_by_code("INVALID_999")
    assert none_course is None


def test_attendance_repository():
    att = AttendanceRepository.get_course_attendance("S1001", "CS201")
    assert att is not None
    assert att["student_id"] == "S1001"
    assert att["course_code"] == "CS201"
    assert att["classes_held"] > 0

    all_att = AttendanceRepository.get_all_student_attendance("S1001")
    assert len(all_att) >= 1


def test_result_repository():
    res = ResultRepository.get_course_result("S1005", "CS201")
    assert res is not None
    assert res["student_id"] == "S1005"
    assert res["course_code"] == "CS201"

    all_res = ResultRepository.get_all_student_results("S1005")
    assert len(all_res) >= 1


def test_rule_repository():
    rules = RuleRepository.get_all_rules()
    assert len(rules) > 0
    rule_ids = [r["rule_id"] for r in rules[:2]]
    subset = RuleRepository.get_rules_by_ids(rule_ids)
    assert len(subset) == len(rule_ids)


def test_audit_repository():
    import uuid
    trace_id = f"test-trace-{uuid.uuid4()}"
    AuditRepository.record_audit(
        trace_id=trace_id,
        student_id="S1001",
        question="Repo test question",
        answer_type="calculated",
        final_answer="Repo test answer",
        latency_ms=5.0,
        model_used="test"
    )

    rec = AuditRepository.get_by_trace_id(trace_id)
    assert rec is not None
    assert rec["trace_id"] == trace_id
    assert rec["question"] == "Repo test question"

    recent = AuditRepository.list_recent(limit=5)
    assert len(recent) >= 1
