# Synthetic Data Card: University Student Services Assistant

## 1. Dataset Overview
- **Dataset Name:** University Student Academic & Attendance Synthetic Dataset
- **Version:** 1.0.0
- **Release Date:** October 2026
- **License:** Open Access / Educational Benchmark
- **Domain:** Higher Education / Academic Administration

> **CRITICAL PRIVACY NOTICE:**
> All student names, registration numbers, academic grades, courses, and attendance statistics in this dataset are **100% synthetically generated**. No real student personal information, identifiable records, or university private records were used, stored, or processed.

---

## 2. Purpose & Objectives
The primary purpose of this dataset is to facilitate realistic, rigorous evaluation of an AI-Powered University Student Services Assistant for the HCLTech Future Ready AI Engineer Hackathon. It enables deterministic verification of:
1. Grounded RAG against official university policy documents.
2. Accurate mathematical calculation of attendance percentages (`(classes_attended / classes_held) * 100`).
3. Multi-parameter rule registry evaluation (exam eligibility, backlog thresholds, CGPA scholarship boundaries).
4. Strict privacy enforcement preventing cross-student data leakage.
5. Deterministic conflict resolution across conflicting and superseded document versions.

---

## 3. Data Generation & Provenance
- **Generator Module:** `app/db/seed.py`
- **Methodology:** Procedural rule-based generation with deterministic seed seeding and deliberate edge-case assignment.
- **Generator LLM / Prompt:** Procedural algorithmic generation in Python using SQLite DDL constraints; no external LLM was permitted to invent ground-truth personal records, ensuring 0% hallucination in ground-truth generation.
- **Schema Validation Method:** SQLite Foreign Key Constraints (`PRAGMA foreign_keys = ON;`), Primary Keys, and Datatype assertions enforced at insertion.

---

## 4. Entity Schemas & Row Counts

| Entity / Table | Primary Key | Total Records | Description |
| :--- | :--- | :--- | :--- |
| **`students`** | `student_id` | **36** (32 synthetic + 4 reserved judge IDs) | Student cohort across 2 programmes and 4 batch years |
| **`courses`** | `course_code` | **8** (6 core + 2 reserved judge courses) | B.Tech CSE & ECE departmental course catalog |
| **`attendance`** | `(student_id, course_code)` | **37** | Classes held, classes attended, and calculation ground truth |
| **`results`** | `(student_id, course_code, exam_session, exam_type)` | **13** | Continuous internal assessment, external marks, total, and pass/fail verdicts |
| **`rule_registry`** | `rule_id` | **7** | Deterministic parameter thresholds mapping to official gazettes |

---

## 5. Deliberate Edge Cases & Cohort Distribution

The dataset was specifically designed to evaluate all critical boundary conditions:

| Case ID | Student ID | Course | Scenario Description | Expected Tool Verdict |
| :--- | :--- | :--- | :--- | :--- |
| **Edge 1** | `S1001` | `CS201` | **Exact Threshold Attendance:** Attended 30/40 classes = **75.0%** | **Eligible** (Satisfies `>= 75.0%`) |
| **Edge 2** | `S1002` | `CS201` | **Below Threshold Attendance:** Attended 29/40 classes = **72.5%** | **Ineligible (Debarred)** (`< 75.0%`) |
| **Edge 3** | `S1003` | `CS201` | **Well Above Threshold Attendance:** Attended 34/40 classes = **85.0%** | **Eligible** (Satisfactory standing) |
| **Edge 4** | `S1004` | `CS201` | **Failed Course (Marks < 40):** Scored 14 int + 18 ext = **32.0/100** | **Result = FAIL** (Backlog recorded) |
| **Edge 5** | `S1005` | `CS201` | **Eligible for Supplementary Exam:** Failed CS201 (35/100), Attendance 80.0%, Backlogs = 1 | **Eligible for Supplementary** (Attendance `>= 75%`, Backlogs `<= 2`) |
| **Edge 6** | `S1006` | `CS201` | **Debarred Ineligible for Supplementary:** Failed CS201 (30/100), Attendance 70.0% | **Ineligible** (Attendance `< 75%` debarred) |
| **Edge 7** | `S1007` | `CS201` | **Excess Backlogs Ineligible:** Failed course, but has **3 active backlogs** | **Ineligible** (Exceeds maximum 2 backlogs) |
| **Edge 8** | `S1008` | `CS201` | **High Merit Standing:** CGPA 9.42, 0 backlogs, Attendance 95.0% | **Eligible for Tier-1 Merit Scholarship** |

---

## 6. Reserved Judge Test Ranges
To allow hackathon judges to verify the system without collision with default cohort data, the following identifiers are strictly reserved:
- **Judge Student IDs:** `99000` through `99999` (Pre-seeded: `99001`, `99002`, `99003`, `99004`)
- **Judge Course Codes:** Course codes prefixed with `JDG` (`JDG101`, `JDG102`)

---

## 7. Known Limitations & Usage Constraints
1. **Scope:** The dataset models undergraduate engineering programmes (B.Tech CSE & B.Tech ECE) and cannot answer questions outside of university student affairs.
2. **Temporal Validity:** Academic regulations are mapped as of academic year 2024-2026. Queries evaluated before July 1, 2024 will reference archived ordinances via source precedence.
