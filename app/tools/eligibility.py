"""
Deterministic Eligibility Calculation Tool.
Evaluates eligibility for regular and supplementary examinations by retrieving rules
from rule_registry and evaluating them against SQLite student, attendance, and result records.
"""

from typing import Any, Dict, List, Optional
from app.tools.student import get_student
from app.tools.attendance import get_attendance
from app.tools.results import get_result
from app.rules.engine import fetch_applicable_rules, evaluate_single_rule


def check_exam_eligibility(
    student_id: str,
    course_code: str,
    exam_type: str = "REGULAR",
    as_of_date: str = "2026-10-06"
) -> Dict[str, Any]:
    student = get_student(student_id)
    if not student:
        return {
            "eligible": False,
            "reason": f"Student '{student_id}' does not exist in university records.",
            "rules_applied": [],
            "sources": []
        }

    att_res = get_attendance(student_id, course_code)
    if not isinstance(att_res, dict) or not att_res.get("found"):
        return {
            "eligible": False,
            "reason": f"Attendance records for course '{course_code}' not found for student '{student_id}'.",
            "rules_applied": [],
            "sources": []
        }

    res_record = get_result(student_id, course_code)
    exam_type_upper = exam_type.upper().strip()

    context = {
        "attendance_percentage": att_res.get("attendance_percentage", 0.0),
        "classes_attended": att_res.get("classes_attended", 0),
        "classes_held": att_res.get("classes_held", 0),
        "cgpa": student.get("cgpa", 0.0),
        "active_backlogs": student.get("active_backlogs", 0),
    }

    if isinstance(res_record, dict) and res_record.get("found"):
        context["total_marks"] = res_record.get("total_marks", 0.0)
        context["result"] = res_record.get("result", "")

    rules_applied: List[Dict[str, Any]] = []
    sources: List[Dict[str, Any]] = []
    failures: List[str] = []

    if exam_type_upper in ["REGULAR", "END_SEM", "END-SEMESTER"]:
        # Rule ATT-MIN-01
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
        # First verify if student actually failed this course
        has_failed = False
        if isinstance(res_record, dict) and res_record.get("found"):
            if res_record.get("result") == "FAIL" or res_record.get("total_marks", 100) < 40.0:
                has_failed = True
        else:
            # If student has backlogs and no pass record
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

        # Fetch supplementary exam rules: SUPP-ELIG-ATT and SUPP-ELIG-BACKLOG
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
