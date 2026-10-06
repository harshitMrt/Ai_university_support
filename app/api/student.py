"""
Student profile and test data endpoints.
"""

from typing import Any, Dict
from fastapi import APIRouter, HTTPException
from app.tools.student import get_student
from app.tools.attendance import get_attendance
from app.tools.results import get_result
from app.db.seed import seed_database

router = APIRouter(tags=["Student Records"])


@router.get("/student/{student_id}")
async def fetch_student_details(student_id: str):
    student = get_student(student_id)
    if not student:
        raise HTTPException(
            status_code=404,
            detail=f"Student record '{student_id}' not found."
        )

    attendance = get_attendance(student_id)
    results = get_result(student_id)

    return {
        "student": student,
        "attendance": attendance,
        "results": results
    }


@router.post("/seed")
async def reload_synthetic_data():
    counts = seed_database()
    return {
        "status": "success",
        "message": "Synthetic student database reseeded successfully.",
        "counts": counts
    }
