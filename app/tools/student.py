"""
Deterministic student data retrieval tool.
Fetches student record exclusively from SQLite.
"""

from typing import Any, Dict, Optional
from app.db.database import get_connection


def get_student(student_id: str) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT student_id, full_name, programme, batch_year, current_semester, cgpa, active_backlogs FROM students WHERE student_id = ?",
        (student_id.strip(),)
    )
    row = cursor.fetchone()
    conn.close()

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
