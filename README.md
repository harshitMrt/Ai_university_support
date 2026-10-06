# AI-Powered University Student Services Assistant

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.38+-FF4B4B.svg)](https://streamlit.io)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.2+-orange.svg)](https://langchain-ai.github.io/langgraph/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

An authoritative, deterministic, and auditable academic assistance platform built for the **HCLTech Future Ready AI Engineer Hackathon**.

The core engineering thesis of this system is that **the LLM is never the source of truth**. Authoritative truth originates strictly from official university publications (indexed in ChromaDB), student academic records (in SQLite), and a deterministic rule registry.

---

## 1. Core Architecture

```
Student / Judge
      │
      ▼
Streamlit Frontend (:8501)
      │  (HTTP + X-Student-Id)
      ▼
FastAPI Backend (:8000)
      │
      ▼
LangGraph 9-Node Pipeline
  ├── 1. classify_intent       (Privacy & prompt-injection checks)
  ├── 2. retrieve_documents     (ChromaDB semantic retrieval + sanitization)
  ├── 3. source_resolution      (Authoritative 5-tier precedence hierarchy)
  ├── 4. select_tool            (Deterministic tool selector)
  ├── 5. execute_tool           (SQLite parameterized queries)
  ├── 6. evaluate_rules         (Rule registry parameter verification)
  ├── 7. synthesize_answer      (Local Ollama LLM grounding strictly on context)
  ├── 8. validate_grounding     (Citation verification & standard abstention)
  └── 9. create_audit_record    (Deterministic audit trace in SQLite)
```

### Key System Guarantees:
- **Zero Hallucination on Personal Data:** Mathematical attendance (`classes_attended / classes_held * 100`), grades, and eligibility are calculated exclusively by deterministic Python/SQLite tools.
- **Strict Source Precedence:** 5-tier document authority hierarchy automatically excludes superseded or expired policies.
- **Privacy By Design:** Student identity is bound to `X-Student-Id`. Queries attempting to access another student's records are immediately refused.
- **Prompt Injection Defense:** Retrieved documents and user queries are sanitized against instruction overrides.
- **Complete Auditability:** Every `/ask` request is recorded with a unique `trace_id` without storing chain-of-thought tokens.

---

## 2. Project Structure

```
.
├── app/
│   ├── main.py                     # FastAPI application entrypoint & lifespan
│   ├── config.py                   # Pydantic environment configuration
│   ├── agent/                      # LangGraph 9-node state machine
│   │   ├── graph.py                # Graph assembly & conditional edges
│   │   ├── nodes.py                # 9 execution nodes
│   │   ├── prompts.py              # Strict grounding system prompts & Ollama client
│   │   └── state.py                # TypedDict AgentState schema
│   ├── api/                        # REST API endpoint routers
│   │   ├── ask.py                  # POST /ask
│   │   ├── ingest.py               # POST /ingest (live multi-part upload)
│   │   ├── health.py               # GET /health
│   │   ├── audit.py                # GET /audit and GET /audit/{trace_id}
│   │   ├── sources.py              # GET /sources
│   │   └── student.py              # GET /student/{student_id} & POST /seed
│   ├── audit/                      # Deterministic trace logger & retrieval
│   ├── db/                         # SQLite database connection & schema
│   │   ├── database.py             # SQLite connection helper
│   │   ├── models.py               # DDL schemas (students, courses, attendance, results, rules, audit)
│   │   └── seed.py                 # 36 synthetic students, 8 courses, deliberate edge cases
│   ├── rag/                        # Persistent ChromaDB vector pipeline
│   │   ├── chunking.py             # Section-aware chunking preserving all 14 metadata fields
│   │   ├── citations.py            # Citation formatting & deduplication
│   │   ├── embeddings.py           # Sentence-Transformers all-MiniLM-L6-v2
│   │   ├── ingest.py               # Document file parsing & ChromaDB persistence
│   │   └── retriever.py            # Cosine similarity vector search
│   ├── rules/
│   │   ├── engine.py               # Deterministic rule evaluator against SQLite
│   │   └── source_precedence.py    # Re-export of source precedence
│   ├── security/
│   │   ├── privacy.py              # Cross-student query detector & identity isolation
│   │   ├── prompt_injection.py     # Inbound prompt injection scanner & document sanitizer
│   │   └── validation.py           # File upload & text length constraints
│   └── tools/                      # Deterministic academic tools
│       ├── attendance.py           # get_attendance(student_id, course_code)
│       ├── eligibility.py          # check_exam_eligibility(student_id, course_code, exam_type)
│       ├── policy.py               # get_course(course_code) & get_applicable_policy(...)
│       ├── results.py              # get_result(student_id, course_code)
│       └── student.py              # get_student(student_id)
├── src/rules/
│   └── source_precedence.py        # Core authoritative source precedence algorithm
├── frontend/
│   └── streamlit_app.py            # Multi-page Streamlit judge interface
├── data/
│   ├── chroma/                     # Persistent ChromaDB vector store
│   ├── documents/                  # Official university policy documents (TXT/PDF)
│   ├── source_register.csv         # Authoritative catalog of all 13 documents
│   └── university.db               # SQLite database
├── evaluation/
│   ├── questions.json              # 20 diverse evaluation test cases
│   └── results/                    # Benchmark run results
├── scripts/
│   ├── load_test_data.py           # Database & ChromaDB reset / initialization script
│   └── run_evaluation.py           # Automated evaluation & benchmark execution script
├── tests/                          # 9 test modules with 31 passing unit tests
├── docs/                           # Technical documentation
│   ├── architecture.md             # Detailed pipeline & data flow specifications
│   ├── api.md                      # REST API endpoints & schemas
│   ├── security.md                 # Threat models & defensive layers
│   └── demo_script.md              # Live judge presentation walkthrough
├── Dockerfile                      # Production container image
├── docker-compose.yml              # Multi-container orchestration
├── requirements.txt                # Python dependencies
└── synthetic_data_card.md          # Synthetic data documentation
```

---

## 3. Quickstart & Setup

### 3.1. Prerequisites
- Python 3.11+
- [Ollama](https://ollama.com/) running locally (tested with `gemma3:270m` or `llama3.2:3b`)

### 3.2. Installation
```bash
# Clone and enter directory
cd "HCL Hackathon"

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3.3. Environment Configuration
Create or inspect `.env` (pre-configured template provided in `.env.example`):
```env
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=gemma3:270m
EMBEDDING_MODEL=all-MiniLM-L6-v2
CHROMA_PATH=./data/chroma
SQLITE_PATH=./data/university.db
DOCUMENT_PATH=./data/documents
SOURCE_REGISTER_PATH=./data/source_register.csv
LOG_LEVEL=INFO
API_PORT=8000
FRONTEND_PORT=8501
```

### 3.4. Initialize Data & Embeddings
```bash
python scripts/load_test_data.py
```
*Seeds 36 students, 8 courses, 37 attendance records, 7 rules, and indexes all 12 university documents into ChromaDB.*

---

## 4. Running the Application

### 4.1. Start Backend (FastAPI)
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```
- API Docs: `http://localhost:8000/docs`
- Health Endpoint: `http://localhost:8000/health`

### 4.2. Start Frontend (Streamlit)
In a second terminal:
```bash
streamlit run frontend/streamlit_app.py --server.port 8501
```
Open `http://localhost:8501` to view the UI.

### 4.3. Docker Compose (Alternative)
```bash
docker compose up --build
```

---

## 5. Automated Tests & Evaluation

### Run Test Suite (31 Unit Tests)
```bash
pytest
```
Tests pass 100% across all 9 required test suites:
- `tests/test_rag.py`
- `tests/test_source_precedence.py`
- `tests/test_attendance.py`
- `tests/test_eligibility.py`
- `tests/test_privacy.py`
- `tests/test_prompt_injection.py`
- `tests/test_api.py`
- `tests/test_ingestion.py`
- `tests/test_audit.py`

### Run 20-Question Benchmark Suite
```bash
python scripts/run_evaluation.py
```
**Benchmark Results:**
- Answer Correctness: **100.0%**
- Citation Accuracy: **100.0%**
- Abstention Accuracy: **100.0%**
- Tool Correctness: **100.0%**
- Retrieval Hit Rate: **100.0%**
- P50 Latency: **~20 ms**
- P95 Latency: **~1,450 ms**

---

## 6. Authoritative Source Precedence Hierarchy

The source precedence engine (`src/rules/source_precedence.py`) guarantees that outdated or conflicting policies are resolved deterministically:

1. **Level 1 (Highest):** Statutes, Ordinances, Academic Regulations (e.g. `ACAD-REG-2024`, `EXAM-REG-2024`)
2. **Level 2:** Official Circulars, Notifications, Authorised Office Documents (e.g. `ATT-POL-2024`, `SUPP-EXAM-2024`)
3. **Level 3:** Department Notices (e.g. `DEPT-CS-2024`)
4. **Level 4:** Student Handbooks & Campus FAQs (e.g. `HANDBOOK-2024`)
5. **Level 5 (Untrusted):** Unofficial content & student forums (e.g. `UNOFF-FORUM-2024`)

### Version Conflict Resolution:
- `ACAD-REG-2021` required 70% attendance.
- `ACAD-REG-2024` requires 75% attendance and explicitly sets `supersedes: ACAD-REG-2021`.
- The engine automatically selects `ACAD-REG-2024` and excludes `ACAD-REG-2021`, documenting the supersession in `policy_notes`.

---

## 7. Streamlit Interface Features

1. **💬 Ask Assistant:** Live chat with quick demo buttons, identity selector (`X-Student-Id`), answer badge (`CALCULATED`, `RETRIEVED FACT`, `REFUSED`, `NOT FOUND`, `CLARIFICATION NEEDED`, `CONFLICT FLAGGED`), trace ID, tools used, rules applied, and clickable citations.
2. **👤 Student Profile:** Real-time view of student demographic data, course attendance, and exam marks fetched from SQLite.
3. **📚 Document Sources:** Master catalog displaying authority level, version, effective date, and supersedes mapping.
4. **📤 Document Ingestion:** Live drag-and-drop document upload indexed into ChromaDB without server restart.
5. **🔍 Audit Explorer:** Search and review execution traces by `trace_id`.
6. **📊 Evaluation Dashboard:** One-click execution of the 20-question benchmark with metric cards and summary table.
7. **🩺 System Health:** Real-time health check of API, SQLite, ChromaDB, and Ollama.

---

## 8. Limitations & Future Work

- **Authentication Mocking:** `X-Student-Id` is received as an HTTP header without cryptographic signature. Production deployment should use OAuth2 / OpenID Connect tokens from university SSO.
- **Adversarial Robustness:** Prompt injection defense uses pattern matching and sanitization. Production systems should add dual-LLM moderation guardrails (e.g. Llama Guard).
- **Single-Node Deployment:** SQLite and ChromaDB run in embedded local modes optimized for low-latency laptop demonstration.
