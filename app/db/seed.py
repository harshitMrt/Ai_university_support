"""
Synthetic Data Generator & Seeder for University Database.
Ensures:
- Over 30 realistic synthetic students
- 2 programmes: B.Tech CSE, B.Tech ECE
- 6 standard courses + 2 reserved judge courses (JDG101, JDG102)
- Specific edge cases:
  1. Attendance exactly 75.0% (S1001)
  2. Attendance below 75.0% e.g. 72.5% (S1002)
  3. Attendance above threshold e.g. 85.0% (S1003)
  4. Failed course (S1004)
  5. Eligible for supplementary (S1005: failed, att=80%, backlogs=1)
  6. Not eligible for supplementary (S1006: failed, att=70%, backlogs=1)
  7. Multiple backlogs > 2 (S1007: backlogs=3)
  8. Different batches (2021, 2022, 2023, 2024)
  9. Different semesters (Sem 3, 4, 5, 6, 7)
- Reserved judge test IDs: 99001, 99002, 99003, 99004
- Rule registry entries mapping to official documents
"""

import sqlite3
from typing import Dict, List, Tuple
from app.db.database import get_connection, init_db


def seed_database() -> Dict[str, int]:
    init_db()
    conn = get_connection()
    cursor = conn.cursor()

    # Clear existing data safely
    cursor.execute("DELETE FROM results;")
    cursor.execute("DELETE FROM attendance;")
    cursor.execute("DELETE FROM courses;")
    cursor.execute("DELETE FROM students;")
    cursor.execute("DELETE FROM rule_registry;")

    # 1. Courses (6 core courses + 2 judge reserved courses)
    courses = [
        ("CS201", "Data Structures and Algorithms", "B.Tech CSE", 3, 4),
        ("CS202", "Database Management Systems", "B.Tech CSE", 4, 4),
        ("CS203", "Operating Systems", "B.Tech CSE", 4, 4),
        ("EC201", "Digital Signal Processing", "B.Tech ECE", 4, 4),
        ("EC202", "Microprocessors and Microcontrollers", "B.Tech ECE", 5, 4),
        ("MA201", "Discrete Mathematics", "B.Tech CSE", 3, 3),
        # Reserved judge courses (beginning with JDG)
        ("JDG101", "Judge Evaluation Protocol", "B.Tech CSE", 8, 3),
        ("JDG102", "Advanced Benchmarking Systems", "B.Tech ECE", 8, 3),
    ]

    cursor.executemany(
        "INSERT INTO courses (course_code, course_name, programme, semester, credits) VALUES (?, ?, ?, ?, ?)",
        courses
    )

    # 2. Students (32 synthetic students + 4 judge test students in 99000-99999 range)
    # student_id, full_name, programme, batch_year, current_semester, cgpa, active_backlogs
    students = [
        # Edge Case 1: S1001 - Attendance exactly at 75.0% in CS201 (30/40)
        ("S1001", "Aarav Sharma", "B.Tech CSE", 2023, 4, 8.12, 0),
        # Edge Case 2: S1002 - Attendance below threshold 72.5% in CS201 (29/40)
        ("S1002", "Diya Patel", "B.Tech CSE", 2023, 4, 7.45, 0),
        # Edge Case 3: S1003 - Attendance well above threshold 85.0% in CS201 (34/40)
        ("S1003", "Rohan Verma", "B.Tech CSE", 2023, 4, 8.88, 0),
        # Edge Case 4: S1004 - Failed CS201 (marks < 40)
        ("S1004", "Ananya Iyer", "B.Tech CSE", 2022, 5, 6.20, 1),
        # Edge Case 5: S1005 - Failed CS201, Attendance 80%, Backlogs=1 -> Eligible for Supplementary
        ("S1005", "Kabir Mehta", "B.Tech CSE", 2022, 5, 6.80, 1),
        # Edge Case 6: S1006 - Failed CS201, Attendance 70% (<75%), Backlogs=1 -> Not eligible for Supp
        ("S1006", "Ishita Nair", "B.Tech CSE", 2022, 5, 5.90, 1),
        # Edge Case 7: S1007 - Active backlogs = 3 (> 2) -> Not eligible for Supplementary / Scholarship
        ("S1007", "Aditya Joshi", "B.Tech CSE", 2021, 7, 5.40, 3),
        # Edge Case 8: S1008 - High CGPA (9.42), 0 backlogs -> Eligible for Merit Scholarship
        ("S1008", "Meera Rao", "B.Tech CSE", 2023, 4, 9.42, 0),
        # Diverse cohorts (B.Tech CSE & B.Tech ECE across 2021, 2022, 2023, 2024)
        ("S1009", "Vikram Singh", "B.Tech ECE", 2023, 4, 7.80, 0),
        ("S1010", "Pooja Reddy", "B.Tech ECE", 2023, 4, 8.55, 0),
        ("S1011", "Kunal Ghosh", "B.Tech ECE", 2022, 6, 7.10, 1),
        ("S1012", "Sneha Kulkarni", "B.Tech CSE", 2024, 2, 8.30, 0),
        ("S1013", "Arjun Deshmukh", "B.Tech CSE", 2024, 2, 7.60, 0),
        ("S1014", "Neha Choudhury", "B.Tech ECE", 2022, 6, 8.90, 0),
        ("S1015", "Rahul Pillai", "B.Tech ECE", 2021, 8, 6.75, 2),
        ("S1016", "Tanvi Bhatia", "B.Tech CSE", 2023, 4, 8.05, 0),
        ("S1017", "Gaurav Sen", "B.Tech CSE", 2022, 6, 7.30, 1),
        ("S1018", "Riya Sen", "B.Tech ECE", 2023, 4, 7.95, 0),
        ("S1019", "Nikhil Saxena", "B.Tech CSE", 2021, 8, 6.40, 2),
        ("S1020", "Priya Menon", "B.Tech ECE", 2024, 2, 8.70, 0),
        ("S1021", "Siddharth Jain", "B.Tech CSE", 2023, 4, 7.15, 0),
        ("S1022", "Kavya Murthy", "B.Tech ECE", 2022, 6, 8.40, 0),
        ("S1023", "Harsh Vardhan", "B.Tech CSE", 2022, 6, 6.95, 1),
        ("S1024", "Simran Kaur", "B.Tech ECE", 2023, 4, 7.75, 0),
        ("S1025", "Manish Pandey", "B.Tech CSE", 2021, 8, 7.20, 0),
        ("S1026", "Swati Mishra", "B.Tech ECE", 2024, 2, 8.10, 0),
        ("S1027", "Alok Kumar", "B.Tech CSE", 2023, 4, 6.85, 2),
        ("S1028", "Shreya Das", "B.Tech ECE", 2022, 6, 7.50, 0),
        ("S1029", "Varun Kapoor", "B.Tech CSE", 2024, 2, 7.90, 0),
        ("S1030", "Deepika Roy", "B.Tech ECE", 2021, 8, 8.25, 0),
        ("S1031", "Aakash Gupta", "B.Tech CSE", 2023, 4, 8.60, 0),
        ("S1032", "Bhavna Mittal", "B.Tech ECE", 2022, 6, 6.50, 1),

        # Reserved Judge Test IDs (99000-99999)
        ("99001", "Judge Test Student Alpha", "B.Tech CSE", 2023, 4, 9.10, 0),
        ("99002", "Judge Test Student Beta (Fail Case)", "B.Tech CSE", 2023, 4, 5.80, 2),
        ("99003", "Judge Test Student Gamma (Low Attendance)", "B.Tech ECE", 2022, 6, 6.20, 1),
        ("99004", "Judge Test Student Delta (High Backlogs)", "B.Tech CSE", 2021, 8, 4.90, 4),

        # Synthetic Test Evaluation Students
        ("STU001", "Aarav Sharma", "B.Tech CSE", 2023, 4, 8.50, 0),
        ("STU002", "Rahul Verma", "B.Tech CSE", 2023, 4, 7.20, 1),
    ]

    cursor.executemany(
        "INSERT INTO students (student_id, full_name, programme, batch_year, current_semester, cgpa, active_backlogs) VALUES (?, ?, ?, ?, ?, ?, ?)",
        students
    )

    # 3. Attendance records (classes_held, classes_attended)
    # Target calculations:
    # S1001 CS201: 30 / 40 = 75.0% (exact)
    # S1002 CS201: 29 / 40 = 72.5% (below)
    # S1003 CS201: 34 / 40 = 85.0% (above)
    # S1004 CS201: 32 / 40 = 80.0%
    # S1005 CS201: 32 / 40 = 80.0%
    # S1006 CS201: 28 / 40 = 70.0% (<75%)
    # S1007 CS201: 25 / 40 = 62.5%
    attendance_records = [
        ("S1001", "CS201", 40, 30),  # 75.0%
        ("S1001", "CS202", 40, 34),  # 85.0%
        ("S1001", "MA201", 30, 26),  # 86.67%

        ("S1002", "CS201", 40, 29),  # 72.5%
        ("S1002", "CS202", 40, 31),  # 77.5%
        ("S1002", "MA201", 30, 22),  # 73.33%

        ("S1003", "CS201", 40, 34),  # 85.0%
        ("S1003", "CS202", 40, 36),  # 90.0%
        ("S1003", "MA201", 30, 28),  # 93.33%

        ("S1004", "CS201", 40, 32),  # 80.0%
        ("S1004", "CS203", 40, 33),  # 82.5%

        ("S1005", "CS201", 40, 32),  # 80.0%
        ("S1005", "CS203", 40, 35),  # 87.5%

        ("S1006", "CS201", 40, 28),  # 70.0%
        ("S1006", "CS203", 40, 30),  # 75.0%

        ("S1007", "CS201", 40, 25),  # 62.5%
        ("S1007", "CS203", 40, 24),  # 60.0%

        ("S1008", "CS201", 40, 38),  # 95.0%
        ("S1008", "CS202", 40, 39),  # 97.5%

        ("S1009", "EC201", 45, 38),  # 84.44%
        ("S1010", "EC201", 45, 41),  # 91.11%
        ("S1011", "EC202", 45, 33),  # 73.33%

        # Populate others with realistic records
        ("S1012", "CS201", 40, 35),
        ("S1013", "CS201", 40, 31),
        ("S1014", "EC201", 45, 42),
        ("S1015", "EC202", 45, 34),
        ("S1016", "CS201", 40, 33),
        ("S1017", "CS203", 40, 31),
        ("S1018", "EC201", 45, 37),
        ("S1019", "CS203", 40, 26),
        ("S1020", "EC201", 45, 43),

        # Reserved judge attendance records
        ("99001", "JDG101", 40, 36),  # 90.0%
        ("99001", "CS201", 40, 34),   # 85.0%
        ("99002", "JDG101", 40, 32),  # 80.0%
        ("99002", "CS201", 40, 31),   # 77.5%
        ("99003", "JDG102", 40, 27),  # 67.5%
        ("99004", "JDG101", 40, 22),  # 55.0%

        # Synthetic test attendance
        ("STU001", "CS201", 40, 34),  # 85.0%
        ("STU001", "CS202", 40, 36),  # 90.0%
        ("STU002", "CS201", 40, 26),  # 65.0%
        ("STU002", "CS202", 40, 24),  # 60.0%
    ]

    cursor.executemany(
        "INSERT INTO attendance (student_id, course_code, classes_held, classes_attended) VALUES (?, ?, ?, ?)",
        attendance_records
    )

    # 4. Results records
    # student_id, course_code, exam_session, exam_type, internal_marks, external_marks, total_marks, max_marks, result
    results = [
        # S1001: Passed CS201 with 78
        ("S1001", "CS201", "Dec 2023", "REGULAR", 32.0, 46.0, 78.0, 100.0, "PASS"),
        ("S1001", "MA201", "Dec 2023", "REGULAR", 35.0, 45.0, 80.0, 100.0, "PASS"),

        # S1002: Passed CS201 with 65
        ("S1002", "CS201", "Dec 2023", "REGULAR", 28.0, 37.0, 65.0, 100.0, "PASS"),

        # S1003: Passed CS201 with 88
        ("S1003", "CS201", "Dec 2023", "REGULAR", 36.0, 52.0, 88.0, 100.0, "PASS"),

        # S1004: Failed CS201 with 32 marks (<40 is FAIL)
        ("S1004", "CS201", "Dec 2023", "REGULAR", 14.0, 18.0, 32.0, 100.0, "FAIL"),

        # S1005: Failed CS201 with 35 marks (<40 is FAIL)
        ("S1005", "CS201", "Dec 2023", "REGULAR", 16.0, 19.0, 35.0, 100.0, "FAIL"),

        # S1006: Failed CS201 with 30 marks (<40 is FAIL)
        ("S1006", "CS201", "Dec 2023", "REGULAR", 12.0, 18.0, 30.0, 100.0, "FAIL"),

        # S1007: Failed CS201 with 25 marks, and CS203 with 28 marks
        ("S1007", "CS201", "Dec 2023", "REGULAR", 10.0, 15.0, 25.0, 100.0, "FAIL"),
        ("S1007", "CS203", "Dec 2023", "REGULAR", 11.0, 17.0, 28.0, 100.0, "FAIL"),

        # S1008: High marks 92
        ("S1008", "CS201", "Dec 2023", "REGULAR", 38.0, 54.0, 92.0, 100.0, "PASS"),

        # Judge results
        ("99001", "JDG101", "May 2024", "REGULAR", 38.0, 55.0, 93.0, 100.0, "PASS"),
        ("99002", "CS201", "Dec 2023", "REGULAR", 15.0, 20.0, 35.0, 100.0, "FAIL"),
        ("99003", "JDG102", "May 2024", "REGULAR", 22.0, 30.0, 52.0, 100.0, "PASS"),

        # Synthetic test results
        ("STU001", "CS201", "Dec 2023", "REGULAR", 34.0, 48.0, 82.0, 100.0, "PASS"),
        ("STU002", "CS201", "Dec 2023", "REGULAR", 14.0, 20.0, 34.0, 100.0, "FAIL"),
    ]

    cursor.executemany(
        "INSERT INTO results (student_id, course_code, exam_session, exam_type, internal_marks, external_marks, total_marks, max_marks, result) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        results
    )

    # 5. Rule Registry
    # rule_id, description, parameter, operator, threshold_value, scope_programmes, scope_batches, effective_from, effective_to, source_doc_id, source_section
    rules = [
        (
            "ATT-MIN-01",
            "Minimum attendance percentage required to appear for end-semester examinations",
            "attendance_percentage",
            ">=",
            75.0,
            "ALL",
            "ALL",
            "2024-07-01",
            None,
            "ACAD-REG-2024",
            "Section 4.1"
        ),
        (
            "EXAM-PASS-01",
            "Minimum aggregate marks required to pass a theory course",
            "total_marks",
            ">=",
            40.0,
            "ALL",
            "ALL",
            "2024-07-01",
            None,
            "EXAM-REG-2024",
            "Section 5.2"
        ),
        (
            "SUPP-ELIG-ATT",
            "Minimum attendance requirement to be eligible for supplementary examination",
            "attendance_percentage",
            ">=",
            75.0,
            "ALL",
            "ALL",
            "2024-07-01",
            None,
            "SUPP-EXAM-2024",
            "Section 2.1"
        ),
        (
            "SUPP-ELIG-BACKLOG",
            "Maximum active backlogs permitted to register for supplementary examinations",
            "active_backlogs",
            "<=",
            2.0,
            "ALL",
            "ALL",
            "2024-07-01",
            None,
            "SUPP-EXAM-2024",
            "Section 2.2"
        ),
        (
            "SCHOL-CGPA-01",
            "Minimum Cumulative Grade Point Average for University Merit Scholarship",
            "cgpa",
            ">=",
            8.5,
            "ALL",
            "ALL",
            "2024-07-01",
            None,
            "SCHOL-POL-2024",
            "Section 3.1"
        ),
        (
            "SCHOL-BACKLOG-01",
            "Maximum active backlogs allowed for scholarship consideration",
            "active_backlogs",
            "<=",
            0.0,
            "ALL",
            "ALL",
            "2024-07-01",
            None,
            "SCHOL-POL-2024",
            "Section 3.2"
        ),
        (
            "HOSTEL-ATT-01",
            "Minimum attendance percentage for hostel room renewal",
            "attendance_percentage",
            ">=",
            80.0,
            "ALL",
            "ALL",
            "2024-07-01",
            None,
            "HOSTEL-2024",
            "Section 6.1"
        )
    ]

    cursor.executemany(
        "INSERT INTO rule_registry (rule_id, description, parameter, operator, threshold_value, scope_programmes, scope_batches, effective_from, effective_to, source_doc_id, source_section) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        rules
    )

    conn.commit()
    conn.close()

    return {
        "students": len(students),
        "courses": len(courses),
        "attendance": len(attendance_records),
        "results": len(results),
        "rules": len(rules)
    }


if __name__ == "__main__":
    counts = seed_database()
    print("Database seeded successfully:", counts)
