"""
Privacy and Authorization Controls for Student Personal Data.
Enforces:
1. Student identity MUST come from request context (X-Student-Id header).
2. Never allow access to another student's records.
3. If an attempt is made to access another student's data, strictly return answer_type = 'refused'.
"""

import re
from typing import Dict, Optional, Tuple

STUDENT_ID_PATTERN = re.compile(r"\b(S\d{4}|99\d{3})\b", re.IGNORECASE)


def inspect_privacy_boundaries(
    question: str,
    authenticated_student_id: Optional[str]
) -> Tuple[bool, Optional[str]]:
    """
    Checks if the question is attempting to query data belonging to a different student.

    Returns:
    (is_violation, refusal_reason)
    """
    if not authenticated_student_id:
        return True, "Authentication required: Missing student identity in request context (X-Student-Id header)."

    auth_id_norm = authenticated_student_id.strip().upper()
    matches = STUDENT_ID_PATTERN.findall(question)

    for match in matches:
        found_id = match.upper()
        if found_id != auth_id_norm:
            return (
                True,
                f"Request refused: Access to personal records of student '{found_id}' is prohibited. "
                "Personal student information cannot be disclosed to other parties under university privacy regulations."
            )

    # Check for phrases inquiring about other students
    other_student_patterns = [
        re.compile(
            r"(another|other|friend's|roommate's|someone else's)\s+(student['’]?s?\s+)?(attendance|marks|grades?|cgpa|backlogs?|results?|records?|details|profile|data)",
            re.IGNORECASE
        ),
        re.compile(
            r"what (is|are)\s+(his|her|their|someone's)\s+(attendance|marks|grades?|cgpa|backlogs?|results?|records?|details)",
            re.IGNORECASE
        ),
        re.compile(
            r"(show|give|display|get)\s+.*(another|other|someone else's)\s+student",
            re.IGNORECASE
        )
    ]

    for p in other_student_patterns:
        if p.search(question):
            return (
                True,
                "Request refused: Personal student information of other students cannot be disclosed under university privacy regulations."
            )

    return False, None
