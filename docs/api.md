# REST API Reference & Contract Specification

The **AI-Powered University Student Services Assistant** provides a clean, deterministic, and auditable REST API built on FastAPI.

**Base URL:** `http://localhost:8000`  
**Interactive Swagger UI:** `http://localhost:8000/docs`  
**OpenAPI Specification:** `http://localhost:8000/openapi.json`

---

## 1. Endpoints Overview

| Method | Endpoint | Description | Auth / Headers |
| :--- | :--- | :--- | :--- |
| `POST` | `/ask` | Ask student assistant query through LangGraph | `X-Student-Id` (Required) |
| `POST` | `/ingest` | Upload & ingest document into ChromaDB in real-time | None |
| `GET` | `/health` | Check operational health across API, SQLite, ChromaDB, Ollama | None |
| `GET` | `/audit/{trace_id}` | Retrieve specific execution audit trace record | None |
| `GET` | `/audit` | List recent execution audit records (paginated) | None |
| `GET` | `/sources` | Retrieve catalog of all registered authoritative documents | None |
| `GET` | `/student/{student_id}` | Retrieve student profile, attendance, and exam results | None |
| `POST` | `/seed` | Reset & reseed synthetic database | None |

---

## 2. Detailed Endpoint Specifications

### 2.1. `POST /ask`
Submits a query to the 9-stage LangGraph student services agent.

#### Headers
- `X-Student-Id` (*string, required*): The identity of the authenticated student making the query (e.g. `S1001`).

#### Request Body
```json
{
  "question": "What is my attendance in CS201?",
  "as_of_date": "2026-10-06"
}
```

#### Response Body (200 OK)
```json
{
  "trace_id": "c76a91d2-28df-45a8-9b7e-976ff1140089",
  "answer_type": "calculated",
  "answer": "Your current attendance in **CS201** (Data Structures and Algorithms) is **75.0%** (30 classes attended out of 40 held). Status: **Satisfactory (Threshold >= 75.0%)** (Mandatory threshold is 75.0%).",
  "citations": [
    {
      "title": "Comprehensive Student Attendance Policy v2.0",
      "doc_id": "ATT-POL-2024",
      "section": "Section 2.1 & 2.2",
      "page": 1,
      "version": "2.0",
      "effective_date": "2024-07-01",
      "authority_level": 2
    }
  ],
  "tools_invoked": [
    "get_student",
    "get_attendance",
    "get_result",
    "get_course"
  ],
  "applied_rules": [],
  "conflicts_detected": [],
  "policy_notes": [],
  "audit_id": "c76a91d2-28df-45a8-9b7e-976ff1140089",
  "latency_ms": 28.4
}
```

#### Answer Types
Every response returns exactly one `answer_type`:
- `calculated`: Personal student metric deterministically computed via SQLite and tools.
- `retrieved_fact`: Factual university policy synthesized from top authoritative source.
- `not_found`: Question cannot be answered by university documents.
- `clarification_needed`: Missing required context (e.g. course code or exam type).
- `refused`: Privacy violations (accessing another student's data) or prompt injections.
- `conflict_flagged`: Unresolvable contradictory policies between equal authorities.

#### Example cURL
```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -H "X-Student-Id: S1001" \
  -d '{"question": "What is the minimum attendance required for the end semester exam?", "as_of_date": "2026-10-06"}'
```

---

### 2.2. `POST /ingest`
Uploads and indexes a new document into ChromaDB without restarting the server.

#### Request Form Data (multipart/form-data)
- `file` (*file, required*): Document file (`.pdf`, `.txt`, `.docx`, `.md`). Maximum 15 MB.
- `doc_id` (*string, optional*): Unique identifier (e.g. `CIRCULAR-2026-01`).
- `title` (*string, optional*): Document title.
- `authority_level` (*int, optional*): 1 (Regulations) to 5 (Unofficial). Default: 2.
- `doc_type` (*string, optional*): Regulation, Policy, Circular, Notice, Handbook.
- `version` (*string, optional*): e.g. `1.0`.
- `effective_from` (*string, optional*): YYYY-MM-DD.
- `effective_to` (*string, optional*): YYYY-MM-DD.
- `supersedes` (*string, optional*): Doc ID superseded by this document.
- `scope_programmes` (*string, optional*): Program scope or `ALL`.
- `scope_batches` (*string, optional*): Batch years or `ALL`.
- `issuer` (*string, optional*): Issuing body.

#### Response Body (200 OK)
```json
{
  "doc_id": "CIRCULAR-2026-01",
  "title": "Dean Special Notification on Attendance",
  "version": "1.0",
  "authority_level": 2,
  "chunks_created": 3,
  "embedding_status": "SUCCESS",
  "metadata": { ... },
  "ingestion_timestamp": "2026-10-06T15:30:00",
  "file_name": "dean_notice.txt"
}
```

---

### 2.3. `GET /health`
Returns dependency status across all system components.

#### Response Body (200 OK)
```json
{
  "status": "ok",
  "api": true,
  "database": true,
  "chromadb": true,
  "ollama": true,
  "model": "gemma3:270m",
  "indexed_chunks": 38
}
```
*Note: If any subsystem is unavailable, returns `status: "degraded"` rather than crashing.*

---

### 2.4. `GET /audit/{trace_id}`
Returns complete audit record for a given trace ID.

#### Response Body (200 OK)
```json
{
  "trace_id": "c76a91d2-28df-45a8-9b7e-976ff1140089",
  "timestamp": "2026-10-06T15:28:10.123456",
  "student_id": "S1001",
  "question": "What is my attendance in CS201?",
  "answer_type": "calculated",
  "selected_sources": [ ... ],
  "retrieved_sources": [ ... ],
  "tools_invoked": [ "get_student", "get_attendance" ],
  "tool_inputs": [ ... ],
  "tool_outputs": [ ... ],
  "rules_applied": [],
  "conflicts_detected": [],
  "model_used": "gemma3:270m",
  "latency_ms": 28.4,
  "final_answer": "Your current attendance in CS201 is 75.0%..."
}
```

---

### 2.5. `GET /sources`
Returns the master catalog of registered authoritative university documents.

---

### 2.6. `GET /student/{student_id}`
Returns student profile, course attendance records, and examination results directly from SQLite.
