"""
Rule Engine module re-export.
Re-exports from app.services.eligibility_service.
"""

from app.services.eligibility_service import (
    OPERATOR_MAP,
    fetch_applicable_rules,
    evaluate_single_rule,
)

__all__ = [
    "OPERATOR_MAP",
    "fetch_applicable_rules",
    "evaluate_single_rule",
]
