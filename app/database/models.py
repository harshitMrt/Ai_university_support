"""
SQLite Schema and Data Models for AI University Student Services Assistant.
Strict adherence to the specified tables and field names:
- students
- courses
- attendance
- results
- rule_registry
- audit_log (for persistence of audit records)
"""

from app.db.models import (
    CREATE_STUDENTS_TABLE,
    CREATE_COURSES_TABLE,
    CREATE_ATTENDANCE_TABLE,
    CREATE_RESULTS_TABLE,
    CREATE_RULE_REGISTRY_TABLE,
    CREATE_AUDIT_LOG_TABLE,
    ALL_TABLE_SCHEMAS,
)

__all__ = [
    "CREATE_STUDENTS_TABLE",
    "CREATE_COURSES_TABLE",
    "CREATE_ATTENDANCE_TABLE",
    "CREATE_RESULTS_TABLE",
    "CREATE_RULE_REGISTRY_TABLE",
    "CREATE_AUDIT_LOG_TABLE",
    "ALL_TABLE_SCHEMAS",
]
