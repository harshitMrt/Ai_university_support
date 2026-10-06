"""
Privacy and Authorization Controls for Student Personal Data.

Core Security & Privacy Principles:
-----------------------------------
1. Identity Isolation:
   - Student identity is NEVER parsed from unauthenticated prompt text.
   - Student identity MUST originate strictly from authenticated HTTP request context (`X-Student-Id` header).
2. Zero Cross-Student Leakage:
   - A logged-in student (e.g., S1001) is strictly forbidden from viewing another student's (e.g., S1002, Rahul's) records.
   - Any query attempting cross-student inspection is blocked immediately before database query execution.
3. Strict Refusal Semantics:
   - Returns answer_type = 'refused' with an explicit ACCESS_DENIED security alert.
   - Does NOT leak whether the requested third-party student exists or has records.
4. Prompt Injection Defense:
   - Rejects adversarial prompts attempting to override privacy rules (e.g., "ignore your privacy rules").
"""

import re
from typing import Dict, Optional, Tuple

# Regex to detect standard student roll number identifiers (e.g., S1001, 99001, STU001)
STUDENT_ID_PATTERN = re.compile(r"\b(S\d{4}|99\d{3}|STU\d{3,5}|STD\d{3,5})\b", re.IGNORECASE)

# Regex to detect phrases specifying another student by ID (e.g., "student STU002")
# Note: requires at least one digit to avoid matching common nouns like "student handbook" or "student withdraws"
EXPLICIT_STUDENT_ID_PATTERN = re.compile(r"\bstudent\s+(?:id\s+)?([A-Za-z]*\d+[A-Za-z0-9]*)\b", re.IGNORECASE)

# Regex to catch prompt injections attempting to disable or override safety checks
PROMPT_INJECTION_PATTERN = re.compile(
    r"\bignore\s+(?:all\s+|your\s+)?(?:privacy|security|authorization|safety|rules|restrictions)\b",
    re.IGNORECASE
)

# Regex patterns matching indirect third-party inquiries (e.g., "my friend's attendance", "Rahul's grades")
OTHER_STUDENT_PATTERNS = [
    # Queries asking for friend's/roommate's/another student's metrics
    re.compile(
        r"(another|other|friend's|roommate's|someone else's)\s+(student['’]?s?\s+)?(attendance|marks|grades?|cgpa|backlogs?|results?|records?|details|profile|data|fee)",
        re.IGNORECASE
    ),
    # Queries asking "what are his/her/their marks"
    re.compile(
        r"what (is|are)\s+(his|her|their|someone's)\s+(attendance|marks|grades?|cgpa|backlogs?|results?|records?|details)",
        re.IGNORECASE
    ),
    # Commands asking to display another student's details
    re.compile(
        r"(show|give|display|get|tell)\s+.*(another|other|someone else's)\s+student",
        re.IGNORECASE
    ),
    # Queries targeting a specific person by name possessive (e.g. "Rahul's attendance")
    re.compile(
        r"\b([A-Z][a-z]+)['’]s\s+(attendance|marks|grades?|cgpa|backlogs?|results?|records?|details|fee)",
        re.IGNORECASE
    ),
    # Queries asking for "attendance of [Person/ID]"
    re.compile(
        r"\b(attendance|marks|grades?|cgpa|backlogs?|results?|records?|fee)\s+of\s+(?:student\s+)?([A-Za-z0-9_-]+)\b",
        re.IGNORECASE
    ),
]


def inspect_privacy_boundaries(
    question: str,
    authenticated_student_id: Optional[str]
) -> Tuple[bool, Optional[str]]:
    """
    Evaluates whether the user's query attempts unauthorized access to another student's confidential data.

    Parameters:
    -----------
    question : str
        The user's submitted query string.
    authenticated_student_id : Optional[str]
        The verified student ID extracted from the HTTP request context.

    Returns:
    --------
    Tuple[bool, Optional[str]]:
        (is_violation, refusal_reason)
        If True, the agent must immediately exit with answer_type = 'refused'.
    """
    # 1. Enforce authentication presence
    if not authenticated_student_id:
        return True, "ACCESS_DENIED: Request refused: Authentication required. Missing student identity in request context (X-Student-Id header)."

    auth_id_norm = authenticated_student_id.strip().upper()

    # 2. Defend against prompt injection overrides
    if PROMPT_INJECTION_PATTERN.search(question):
        return (
            True,
            "ACCESS_DENIED: Request refused: Prompt injection or security rule override detected. Unauthorized access to student personal records is strictly prohibited."
        )

    # 3. Detect unauthorized student ID tokens in query text
    matches = STUDENT_ID_PATTERN.findall(question)
    for match in matches:
        found_id = match.upper()
        # If the queried student ID does not match the authenticated session, reject!
        if found_id != auth_id_norm:
            return (
                True,
                f"ACCESS_DENIED: Request refused: Access to personal records of student '{found_id}' is prohibited. "
                "Personal student information cannot be disclosed to other parties under university privacy regulations."
            )

    # 4. Detect explicit student references (e.g. "student STU002")
    explicit_matches = EXPLICIT_STUDENT_ID_PATTERN.findall(question)
    for match in explicit_matches:
        found_id = match.upper()
        if found_id != auth_id_norm and not found_id.startswith("POLICY") and not found_id.startswith("RULE"):
            return (
                True,
                f"ACCESS_DENIED: Request refused: Access to personal records of student '{found_id}' is prohibited. "
                "Personal student information cannot be disclosed to other parties under university privacy regulations."
            )

    # 5. Detect queries inquiring about third-party students or named individuals
    for p in OTHER_STUDENT_PATTERNS:
        m = p.search(question)
        if m:
            target = m.group(1).lower() if m.lastindex else ""
            # Ignore false positives on generic academic vocabulary
            if target in ["my", "the", "a", "all", "minimum", "course", "exam", "theory", "lab"]:
                continue
            return (
                True,
                "ACCESS_DENIED: Request refused: Personal student information of other students cannot be disclosed under university privacy regulations."
            )

    # All security and privacy boundaries satisfied
    return False, None
