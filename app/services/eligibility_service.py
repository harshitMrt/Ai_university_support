"""
Deterministic Eligibility Calculation Service.
Evaluates eligibility for regular and supplementary examinations by retrieving rules
from rule_registry via RuleRepository and evaluating them against SQLite student,
attendance, and result records.
"""

import operator
from typing import Any, Dict, List, Optional
from app.repositories.student_repository import StudentRepository
from app.repositories.attendance_repository import AttendanceRepository
from app.repositories.result_repository import ResultRepository
from app.repositories.rule_repository import RuleRepository

OPERATOR_MAP = {
    ">=": operator.ge,
    "<=": operator.le,
    ">": operator.gt,
    "<": operator.lt,
    "==": operator.eq,
    "!=": operator.ne,
    "=": operator.eq,
}


def fetch_applicable_rules(
    rule_ids: Optional[List[str]] = None,
    programme: Optional[str] = None,
    batch_year: Optional[int] = None,
    as_of_date: Optional[str] = "2026-10-06"
) -> List[Dict[str, Any]]:
    """
    Queries rule_registry and filters rules matching the given execution context.
    """
    if rule_ids:
        rows = RuleRepository.get_rules_by_ids(rule_ids)
    else:
        rows = RuleRepository.get_all_rules()

    applicable = []
    for r in rows:
        rid = r["rule_id"]
        if rule_ids and rid not in rule_ids:
            continue

        eff_from = r.get("effective_from")
        eff_to = r.get("effective_to")
        if as_of_date:
            if eff_from and as_of_date < eff_from:
                continue
            if eff_to and as_of_date > eff_to:
                continue

        scope_p = r.get("scope_programmes", "ALL")
        if programme and scope_p != "ALL" and programme.lower() not in scope_p.lower():
            continue

        scope_b = str(r.get("scope_batches", "ALL"))
        if batch_year and scope_b != "ALL" and str(batch_year) not in scope_b:
            continue

        applicable.append(dict(r))

    return applicable


def evaluate_single_rule(
    rule: Dict[str, Any],
    context: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Deterministically evaluates an individual policy threshold against a student's context values.
    """
    param_name = rule["parameter"]
    op_str = rule["operator"].strip()
    threshold = float(rule["threshold_value"]) if rule.get("threshold_value") is not None else 0.0

    actual_val = context.get(param_name)
    if actual_val is None:
        return {
            "rule_id": rule["rule_id"],
            "description": rule["description"],
            "parameter": param_name,
            "operator": op_str,
            "threshold": threshold,
            "actual_value": None,
            "passed": False,
            "reason": f"Required parameter '{param_name}' not available in student context."
        }

    actual_val = float(actual_val)
    op_fn = OPERATOR_MAP.get(op_str)

    if not op_fn:
        return {
            "rule_id": rule["rule_id"],
            "description": rule["description"],
            "parameter": param_name,
            "operator": op_str,
            "threshold": threshold,
            "actual_value": actual_val,
            "passed": False,
            "reason": f"Unsupported operator '{op_str}'."
        }

    passed = op_fn(actual_val, threshold)

    return {
        "rule_id": rule["rule_id"],
        "description": rule["description"],
        "parameter": param_name,
        "operator": op_str,
        "threshold": threshold,
        "actual_value": actual_val,
        "passed": bool(passed),
        "source_doc_id": rule.get("source_doc_id"),
        "source_section": rule.get("source_section"),
        "reason": f"{param_name} ({actual_val}) {op_str} {threshold} is {'SATISFIED' if passed else 'VIOLATED'}."
    }


def check_exam_eligibility(
    student_id: str,
    course_code: str,
    exam_type: str = "REGULAR",
    as_of_date: str = "2026-10-06"
) -> Dict[str, Any]:
    student = StudentRepository.get_by_id(student_id)
    if not student:
        return {
            "eligible": False,
            "reason": f"Student '{student_id}' does not exist in university records.",
            "rules_applied": [],
            "sources": []
        }

    att_row = AttendanceRepository.get_course_attendance(student_id, course_code)
    if not att_row:
        return {
            "eligible": False,
            "reason": f"Attendance records for course '{course_code}' not found for student '{student_id}'.",
            "rules_applied": [],
            "sources": []
        }

    held = att_row.get("classes_held", 0)
    attended = att_row.get("classes_attended", 0)
    att_pct = round((attended / held * 100.0), 2) if held > 0 else 0.0

    res_record = ResultRepository.get_course_result(student_id, course_code)
    exam_type_upper = exam_type.upper().strip()

    context = {
        "attendance_percentage": att_pct,
        "classes_attended": attended,
        "classes_held": held,
        "cgpa": student.get("cgpa", 0.0),
        "active_backlogs": student.get("active_backlogs", 0),
    }

    if res_record:
        context["total_marks"] = res_record.get("total_marks", 0.0)
        context["result"] = res_record.get("result", "")

    rules_applied: List[Dict[str, Any]] = []
    sources: List[Dict[str, Any]] = []
    failures: List[str] = []

    if exam_type_upper in ["REGULAR", "END_SEM", "END-SEMESTER"]:
        rules = fetch_applicable_rules(
            rule_ids=["ATT-MIN-01"],
            programme=student.get("programme"),
            batch_year=student.get("batch_year"),
            as_of_date=as_of_date
        )
        for r in rules:
            eval_res = evaluate_single_rule(r, context)
            rules_applied.append(eval_res)
            sources.append({
                "doc_id": r.get("source_doc_id"),
                "section": r.get("source_section"),
                "rule_id": r.get("rule_id")
            })
            if not eval_res["passed"]:
                failures.append(
                    f"Attendance of {context['attendance_percentage']}% is below the mandatory {eval_res['threshold']}% threshold (Rule {r['rule_id']})."
                )

        eligible = len(failures) == 0
        if eligible:
            reason = f"Student meets all requirements: attendance is {context['attendance_percentage']}%, satisfying the minimum 75.0% threshold."
        else:
            reason = "Ineligible for End-Semester Exam: " + "; ".join(failures) + " Resulting in Grade 'AD' (Attendance Debarred)."

        return {
            "eligible": eligible,
            "student_id": student_id,
            "course_code": course_code,
            "exam_type": "REGULAR",
            "attendance_percentage": context["attendance_percentage"],
            "reason": reason,
            "rules_applied": rules_applied,
            "sources": sources
        }

    elif exam_type_upper in ["SUPPLEMENTARY", "SUPP", "BACKLOG"]:
        has_failed = False
        if res_record:
            if res_record.get("result") == "FAIL" or res_record.get("total_marks", 100) < 40.0:
                has_failed = True
        else:
            if student.get("active_backlogs", 0) > 0:
                has_failed = True

        if not has_failed:
            return {
                "eligible": False,
                "student_id": student_id,
                "course_code": course_code,
                "exam_type": "SUPPLEMENTARY",
                "reason": f"Student has already passed course '{course_code}' or has no recorded failure. Supplementary exam is only permitted for failed courses.",
                "rules_applied": [],
                "sources": [{
                    "doc_id": "SUPP-EXAM-2024",
                    "section": "Section 2.3",
                    "rule_id": "SUPP-FAIL-REQ"
                }]
            }

        supp_rules = fetch_applicable_rules(
            rule_ids=["SUPP-ELIG-ATT", "SUPP-ELIG-BACKLOG"],
            programme=student.get("programme"),
            batch_year=student.get("batch_year"),
            as_of_date=as_of_date
        )

        for r in supp_rules:
            eval_res = evaluate_single_rule(r, context)
            rules_applied.append(eval_res)
            sources.append({
                "doc_id": r.get("source_doc_id"),
                "section": r.get("source_section"),
                "rule_id": r.get("rule_id")
            })
            if not eval_res["passed"]:
                if r["parameter"] == "attendance_percentage":
                    failures.append(
                        f"Attendance of {context['attendance_percentage']}% is below the mandatory {eval_res['threshold']}% threshold (Rule {r['rule_id']}). Debarred students cannot write supplementary exams."
                    )
                elif r["parameter"] == "active_backlogs":
                    failures.append(
                        f"Active backlogs count ({context['active_backlogs']}) exceeds the maximum permissible limit of {eval_res['threshold']} (Rule {r['rule_id']})."
                    )
                else:
                    failures.append(eval_res["reason"])

        eligible = len(failures) == 0
        if eligible:
            reason = (
                f"Eligible for Supplementary Exam: Student failed course '{course_code}', "
                f"attendance ({context['attendance_percentage']}%) meets the >= 75.0% requirement, "
                f"and active backlogs ({context['active_backlogs']}) are within the limit (<= 2)."
            )
        else:
            reason = "Not eligible for Supplementary Exam: " + "; ".join(failures)

        return {
            "eligible": eligible,
            "student_id": student_id,
            "course_code": course_code,
            "exam_type": "SUPPLEMENTARY",
            "attendance_percentage": context["attendance_percentage"],
            "active_backlogs": context["active_backlogs"],
            "reason": reason,
            "rules_applied": rules_applied,
            "sources": sources
        }

    else:
        return {
            "eligible": False,
            "reason": f"Unknown exam type: '{exam_type}'. Supported types: REGULAR, SUPPLEMENTARY.",
            "rules_applied": [],
            "sources": []
        }
