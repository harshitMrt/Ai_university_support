"""
Deterministic Eligibility Calculation Tool.
Re-exports from app.services.eligibility_service.
"""

from app.services.eligibility_service import check_exam_eligibility

__all__ = ["check_exam_eligibility"]
