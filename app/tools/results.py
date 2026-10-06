"""
Deterministic exam results and marks tool.
Retrieves student examination results directly from SQLite via ResultRepository.
"""

from typing import Any, Dict, List, Optional, Union
from app.repositories.result_repository import ResultRepository


def get_result(
    student_id: str,
    course_code: Optional[str] = None
) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
    if course_code:
        record = ResultRepository.get_course_result(student_id, course_code)
        if not record:
            return {
                "error": f"Result record not found for student '{student_id}' in course '{course_code}'.",
                "student_id": student_id,
                "course_code": course_code,
                "found": False
            }
        record["found"] = True
        return record
    else:
        results_list = ResultRepository.get_all_student_results(student_id)
        return {
            "student_id": student_id,
            "results": results_list,
            "count": len(results_list),
            "found": len(results_list) > 0
        }
