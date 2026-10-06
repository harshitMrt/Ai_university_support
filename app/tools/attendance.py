"""
Deterministic attendance calculation tool.
Strictly calculates:
attendance_percentage = (classes_attended / classes_held) * 100
Never delegates math or calculation to the LLM.
Retrieves data via AttendanceRepository.
"""

from typing import Any, Dict, List, Optional, Union
from app.repositories.attendance_repository import AttendanceRepository


def get_attendance(
    student_id: str,
    course_code: Optional[str] = None
) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
    if course_code:
        record = AttendanceRepository.get_course_attendance(student_id, course_code)
        if not record:
            return {
                "error": f"Attendance record not found for student '{student_id}' in course '{course_code}'.",
                "student_id": student_id,
                "course_code": course_code,
                "found": False
            }

        classes_held = record["classes_held"]
        classes_attended = record["classes_attended"]
        pct = round((classes_attended / classes_held * 100.0), 2) if classes_held > 0 else 0.0

        return {
            "student_id": record["student_id"],
            "course_code": record["course_code"],
            "course_name": record.get("course_name", ""),
            "classes_held": classes_held,
            "classes_attended": classes_attended,
            "attendance_percentage": pct,
            "status": "Shortage" if pct < 75.0 else "Satisfactory",
            "found": True
        }
    else:
        rows = AttendanceRepository.get_all_student_attendance(student_id)
        if not rows:
            return {
                "error": f"No attendance records found for student '{student_id}'.",
                "student_id": student_id,
                "courses": [],
                "found": False
            }

        courses_data = []
        total_held = 0
        total_attended = 0

        for r in rows:
            held = r["classes_held"]
            att = r["classes_attended"]
            pct = round((att / held * 100.0), 2) if held > 0 else 0.0
            total_held += held
            total_attended += att
            courses_data.append({
                "course_code": r["course_code"],
                "course_name": r.get("course_name", ""),
                "classes_held": held,
                "classes_attended": att,
                "attendance_percentage": pct,
                "status": "Shortage" if pct < 75.0 else "Satisfactory"
            })

        overall_pct = round((total_attended / total_held * 100.0), 2) if total_held > 0 else 0.0

        return {
            "student_id": student_id,
            "courses": courses_data,
            "total_classes_held": total_held,
            "total_classes_attended": total_attended,
            "overall_attendance_percentage": overall_pct,
            "status": "Shortage" if overall_pct < 75.0 else "Satisfactory",
            "found": True
        }
