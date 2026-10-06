"""
Repository for student profile and course queries against SQLite.
Ensures parameterized, injection-safe database access.
"""

from typing import Any, Dict, List, Optional
from app.database.connection import get_connection


class StudentRepository:
    @staticmethod
    def get_by_id(student_id: str) -> Optional[Dict[str, Any]]:
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT student_id, full_name, programme, batch_year, current_semester, cgpa, active_backlogs
                FROM students
                WHERE student_id = ?
                """,
                (student_id.strip(),)
            )
            row = cursor.fetchone()
            if not row:
                return None
            return {
                "student_id": row["student_id"],
                "full_name": row["full_name"],
                "programme": row["programme"],
                "batch_year": int(row["batch_year"]),
                "current_semester": int(row["current_semester"]),
                "cgpa": float(row["cgpa"]),
                "active_backlogs": int(row["active_backlogs"]),
            }
        finally:
            conn.close()

    @staticmethod
    def get_course_by_code(course_code: str) -> Optional[Dict[str, Any]]:
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT course_code, course_name, programme, semester, credits
                FROM courses
                WHERE UPPER(course_code) = UPPER(?)
                """,
                (course_code.strip(),)
            )
            row = cursor.fetchone()
            if not row:
                return None
            return {
                "course_code": row["course_code"],
                "course_name": row["course_name"],
                "programme": row["programme"],
                "semester": int(row["semester"]),
                "credits": int(row["credits"]),
            }
        finally:
            conn.close()

    @staticmethod
    def list_all_students(limit: int = 100) -> List[Dict[str, Any]]:
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT student_id, full_name, programme, batch_year, current_semester, cgpa, active_backlogs FROM students LIMIT ?",
                (limit,)
            )
            return [dict(r) for r in cursor.fetchall()]
        finally:
            conn.close()
