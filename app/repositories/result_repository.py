"""
Repository for student examination results and grade records in SQLite.
"""

from typing import Any, Dict, List, Optional
from app.database.connection import get_connection


class ResultRepository:
    @staticmethod
    def get_course_result(student_id: str, course_code: str) -> Optional[Dict[str, Any]]:
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT r.student_id, r.course_code, c.course_name, r.exam_session, r.exam_type,
                       r.internal_marks, r.external_marks, r.total_marks, r.max_marks, r.result
                FROM results r
                LEFT JOIN courses c ON r.course_code = c.course_code
                WHERE r.student_id = ? AND UPPER(r.course_code) = UPPER(?)
                ORDER BY r.rowid DESC
                LIMIT 1
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
                "exam_session": row["exam_session"],
                "exam_type": row["exam_type"],
                "internal_marks": float(row["internal_marks"]),
                "external_marks": float(row["external_marks"]),
                "total_marks": float(row["total_marks"]),
                "max_marks": float(row["max_marks"]),
                "result": row["result"],
            }
        finally:
            conn.close()

    @staticmethod
    def get_all_student_results(student_id: str) -> List[Dict[str, Any]]:
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT r.student_id, r.course_code, c.course_name, r.exam_session, r.exam_type,
                       r.internal_marks, r.external_marks, r.total_marks, r.max_marks, r.result
                FROM results r
                LEFT JOIN courses c ON r.course_code = c.course_code
                WHERE r.student_id = ?
                ORDER BY r.course_code
                """,
                (student_id.strip(),)
            )
            rows = cursor.fetchall()
            return [
                {
                    "course_code": r["course_code"],
                    "course_name": r["course_name"] or "",
                    "exam_session": r["exam_session"],
                    "exam_type": r["exam_type"],
                    "internal_marks": float(r["internal_marks"]),
                    "external_marks": float(r["external_marks"]),
                    "total_marks": float(r["total_marks"]),
                    "max_marks": float(r["max_marks"]),
                    "result": r["result"],
                }
                for r in rows
            ]
        finally:
            conn.close()
