"""
Course details and academic lookup tools.
Fetches course records exclusively from SQLite using StudentRepository.
"""

from typing import Any, Dict, Optional
from app.repositories.student_repository import StudentRepository


def get_course(course_code: str) -> Optional[Dict[str, Any]]:
    return StudentRepository.get_course_by_code(course_code)
