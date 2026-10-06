"""
Deterministic attendance calculation tool.
Strictly calculates:
attendance_percentage = (classes_attended / classes_held) * 100
Never delegates math or calculation to the LLM.
"""

from typing import Any, Dict, List, Optional, Union
from app.db.database import get_connection


def get_attendance(
    student_id: str,
    course_code: Optional[str] = None
) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
    conn = get_connection()
    cursor = conn.cursor()

    if course_code:
        cursor.execute(
            """
            SELECT a.student_id, a.course_code, c.course_name, a.classes_held, a.classes_attended
            FROM attendance a
            LEFT JOIN courses c ON a.course_code = c.course_code
            WHERE a.student_id = ? AND UPPER(a.course_code) = UPPER(?)
            """,
            (student_id.strip(), course_code.strip())
        )
        row = cursor.fetchone()
        conn.close()

        if not row:
            return {
                "error": f"Attendance record not found for student '{student_id}' in course '{course_code}'.",
                "student_id": student_id,
                "course_code": course_code,
                "found": False
            }

        classes_held = int(row["classes_held"])
        classes_attended = int(row["classes_attended"])
        pct = round((classes_attended / classes_held * 100.0), 2) if classes_held > 0 else 0.0

        return {
            "student_id": row["student_id"],
            "course_code": row["course_code"],
            "course_name": row["course_name"] or "",
            "classes_held": classes_held,
            "classes_attended": classes_attended,
            "attendance_percentage": pct,
            "status": "Shortage" if pct < 75.0 else "Satisfactory",
            "found": True
        }
    else:
        # Aggregate all courses for student
        cursor.execute(
            """
            SELECT a.student_id, a.course_code, c.course_name, a.classes_held, a.classes_attended
            FROM attendance a
            LEFT JOIN courses c ON a.course_code = c.course_code
            WHERE a.student_id = ?
            ORDER BY a.course_code
            """,
            (student_id.strip(),)
        )
        rows = cursor.fetchall()
        conn.close()

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
            held = int(r["classes_held"])
            att = int(r["classes_attended"])
            pct = round((att / held * 100.0), 2) if held > 0 else 0.0
            total_held += held
            total_attended += att
            courses_data.append({
                "course_code": r["course_code"],
                "course_name": r["course_name"] or "",
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
