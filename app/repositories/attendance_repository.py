"""
Repository for student attendance records in SQLite.
"""

from typing import Any, Dict, List, Optional
from app.database.connection import get_connection


class AttendanceRepository:
    @staticmethod
    def get_course_attendance(student_id: str, course_code: str) -> Optional[Dict[str, Any]]:
        conn = get_connection()
        try:
            cursor = conn.cursor()
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
            if not row:
                return None
            return {
                "student_id": row["student_id"],
                "course_code": row["course_code"],
                "course_name": row["course_name"] or "",
                "classes_held": int(row["classes_held"]),
                "classes_attended": int(row["classes_attended"]),
            }
        finally:
            conn.close()

    @staticmethod
    def get_all_student_attendance(student_id: str) -> List[Dict[str, Any]]:
        conn = get_connection()
        try:
            cursor = conn.cursor()
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
            return [
                {
                    "student_id": r["student_id"],
                    "course_code": r["course_code"],
                    "course_name": r["course_name"] or "",
                    "classes_held": int(r["classes_held"]),
                    "classes_attended": int(r["classes_attended"]),
                }
                for r in rows
            ]
        finally:
            conn.close()
