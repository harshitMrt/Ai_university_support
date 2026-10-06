# System Architecture & Technical Specifications

## 1. High-Level Architecture Overview

The **AI-Powered University Student Services Assistant** is engineered around the principle that **the LLM is never the source of truth**. Ground truth originates strictly from official university publications (indexed in ChromaDB), student academic databases (SQLite), and the deterministic rule registry.

```mermaid
graph TD
    User([Student / Judge]) -->|HTTP Request + X-Student-Id| Streamlit[Streamlit UI :8501]
    Streamlit -->|REST API Calls| FastAPI[FastAPI Backend :8000]
    
    subgraph "Core Agent Orchestration (LangGraph)"
        FastAPI --> Node1[1. Classify Intent & Security Check]
        Node1 -->|Safe & Clear| Node2[2. Semantic Document Retrieval]
        Node1 -->|Refusal / Clarification| Node9[9. Create Audit Record]
        
        Node2 --> Node3[3. Authoritative Source Precedence]
        Node3 --> Node4[4. Deterministic Tool Selector]
        Node4 --> Node5[5. Tool Execution Engine]
        Node5 --> Node6[6. Rule Registry Evaluator]
        Node6 --> Node7[7. Grounded Answer Synthesis]
        Node7 --> Node8[8. Grounding & Citation Validator]
        Node8 --> Node9
    end

    subgraph "Deterministic & Vector Data Sources"
        Node2 <--> Chroma[(ChromaDB Vector Store)]
        Chroma <--> Embedder[Sentence-Transformers all-MiniLM-L6-v2]
        Embedder <--> Documents[(Official University Documents)]
        
        Node5 <--> SQLite[(SQLite Database)]
        Node6 <--> SQLite
        Node9 --> SQLite
    end

    subgraph "Local LLM Synthesis"
        Node7 <--> Ollama[Ollama Local LLM gemma3:270m]
    end

    Node9 -->|Grounded Response + Audit Record| FastAPI
```

---

## 2. Nine-Node LangGraph Orchestration Pipeline

| Step | Node Name | Purpose & Behavioral Guarantees |
| :--- | :--- | :--- |
| **1** | `classify_intent` | Inspects privacy boundaries (`X-Student-Id` isolation), scans for prompt injection patterns, identifies target courses (`CS201`, `EC201`, etc.) and determines required intent. Early-exits safely on violations. |
| **2** | `retrieve_documents` | Queries ChromaDB for top semantic chunks, defangs any prompt injection patterns in retrieved text via the document safety layer. |
| **3** | `source_resolution` | Executes `resolve_authoritative_sources` from `src/rules/source_precedence.py` enforcing the 6-level hierarchy, supersession rules, and conflict detection. |
| **4** | `select_tool` | Maps required intent to deterministic tool calls (`get_student`, `get_attendance`, `get_result`, `check_exam_eligibility`). |
| **5** | `execute_tool` | Queries SQLite deterministically to compute exact percentages and student standings without invoking the LLM. |
| **6** | `evaluate_rules` | Evaluates dynamic rules from `rule_registry` in SQLite (e.g. `ATT-MIN-01`, `SUPP-ELIG-ATT`, `SUPP-ELIG-BACKLOG`). |
| **7** | `synthesize_answer` | Generates a grounded, natural-language explanation strictly citing official document sections, version, and tool outputs. |
| **8** | `validate_grounding` | Verifies that citations exist, no hallucinations occurred, and enforces the standard abstention string if facts are absent. |
| **9** | `create_audit_record` | Logs trace ID, latency, sources, tools, rules, and answer into SQLite `audit_log` without storing intermediate chain-of-thought. |

---

## 3. Document Authority & Precedence Resolution Hierarchy

Documents are categorized across 5 distinct authority tiers:

| Authority Level | Document Classification | Examples |
| :---: | :--- | :--- |
| **Level 1 (Highest)** | Statutes, Ordinances, Academic Regulations | `ACAD-REG-2024` (v3.1), `EXAM-REG-2024` (v2.5) |
| **Level 2** | Official Circulars, Notifications, Authorised Policies | `ATT-POL-2024` (v2.0), `SUPP-EXAM-2024` (v1.8) |
| **Level 3** | Departmental Notices & Guidelines | `DEPT-CS-2024` (v1.2) |
| **Level 4** | Student Handbooks & Campus FAQs | `HANDBOOK-2024` (v4.0) |
| **Level 5 (Untrusted)** | Student Forums, Social Media & Unofficial Content | `UNOFF-FORUM-2024` (v0.9) |

### Resolution Algorithm:
1. **Active Effective Date:** Excludes expired documents (`as_of_date > effective_to`) or premature documents (`effective_from > as_of_date`).
2. **Scope Match:** Prefers policies specifically scoping the student's programme (e.g. `B.Tech CSE`) or batch.
3. **Explicit Supersession:** When document A specifies `supersedes: B`, document B is disqualified regardless of its historical status.
4. **Authority Dominance:** Higher authority tiers supersede lower tiers when scopes overlap.
5. **Enactment Recency:** When authority levels are equal, the more recently effective policy wins.
6. **Conflict Flagging:** If two policies of equal tier contradict each other without supersession, the system flags `answer_type = "conflict_flagged"`.
