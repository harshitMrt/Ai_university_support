"""
Deterministic student data retrieval tool.
Fetches student record exclusively from SQLite using StudentRepository.
"""

from typing import Any, Dict, Optional
from app.repositories.student_repository import StudentRepository


def get_student(student_id: str) -> Optional[Dict[str, Any]]:
    return StudentRepository.get_by_id(student_id)
