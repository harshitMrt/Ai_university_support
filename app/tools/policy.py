"""
Course details and academic lookup tools.
"""

from typing import Any, Dict, Optional
from app.db.database import get_connection


def get_course(course_code: str) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT course_code, course_name, programme, semester, credits FROM courses WHERE UPPER(course_code) = UPPER(?)",
        (course_code.strip(),)
    )
    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    return {
        "course_code": row["course_code"],
        "course_name": row["course_name"],
        "programme": row["programme"],
        "semester": int(row["semester"]),
        "credits": int(row["credits"]),
    }
