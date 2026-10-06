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

CREATE_STUDENTS_TABLE = """
CREATE TABLE IF NOT EXISTS students (
    student_id TEXT PRIMARY KEY,
    full_name TEXT NOT NULL,
    programme TEXT NOT NULL,
    batch_year INTEGER NOT NULL,
    current_semester INTEGER NOT NULL,
    cgpa REAL NOT NULL,
    active_backlogs INTEGER NOT NULL DEFAULT 0
);
"""

CREATE_COURSES_TABLE = """
CREATE TABLE IF NOT EXISTS courses (
    course_code TEXT PRIMARY KEY,
    course_name TEXT NOT NULL,
    programme TEXT NOT NULL,
    semester INTEGER NOT NULL,
    credits INTEGER NOT NULL
);
"""

CREATE_ATTENDANCE_TABLE = """
CREATE TABLE IF NOT EXISTS attendance (
    student_id TEXT NOT NULL,
    course_code TEXT NOT NULL,
    classes_held INTEGER NOT NULL,
    classes_attended INTEGER NOT NULL,
    PRIMARY KEY (student_id, course_code),
    FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE,
    FOREIGN KEY (course_code) REFERENCES courses(course_code) ON DELETE CASCADE
);
"""

CREATE_RESULTS_TABLE = """
CREATE TABLE IF NOT EXISTS results (
    student_id TEXT NOT NULL,
    course_code TEXT NOT NULL,
    exam_session TEXT NOT NULL,
    exam_type TEXT NOT NULL,
    internal_marks REAL NOT NULL,
    external_marks REAL NOT NULL,
    total_marks REAL NOT NULL,
    max_marks REAL NOT NULL DEFAULT 100.0,
    result TEXT NOT NULL,
    PRIMARY KEY (student_id, course_code, exam_session, exam_type),
    FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE,
    FOREIGN KEY (course_code) REFERENCES courses(course_code) ON DELETE CASCADE
);
"""

CREATE_RULE_REGISTRY_TABLE = """
CREATE TABLE IF NOT EXISTS rule_registry (
    rule_id TEXT PRIMARY KEY,
    description TEXT NOT NULL,
    parameter TEXT NOT NULL,
    operator TEXT NOT NULL,
    threshold_value REAL,
    scope_programmes TEXT NOT NULL DEFAULT 'ALL',
    scope_batches TEXT NOT NULL DEFAULT 'ALL',
    effective_from TEXT NOT NULL,
    effective_to TEXT,
    source_doc_id TEXT NOT NULL,
    source_section TEXT NOT NULL
);
"""

CREATE_AUDIT_LOG_TABLE = """
CREATE TABLE IF NOT EXISTS audit_log (
    trace_id TEXT PRIMARY KEY,
    timestamp TEXT NOT NULL,
    student_id TEXT NOT NULL,
    question TEXT NOT NULL,
    answer_type TEXT NOT NULL,
    selected_sources TEXT,
    retrieved_sources TEXT,
    tools_invoked TEXT,
    tool_inputs TEXT,
    tool_outputs TEXT,
    rules_applied TEXT,
    conflicts_detected TEXT,
    model_used TEXT,
    latency_ms REAL,
    final_answer TEXT
);
"""

ALL_TABLE_SCHEMAS = [
    CREATE_STUDENTS_TABLE,
    CREATE_COURSES_TABLE,
    CREATE_ATTENDANCE_TABLE,
    CREATE_RESULTS_TABLE,
    CREATE_RULE_REGISTRY_TABLE,
    CREATE_AUDIT_LOG_TABLE,
]
