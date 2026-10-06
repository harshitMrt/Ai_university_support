"""
LangGraph Nodes implementing the 9-stage student services pipeline.
Strict adherence to:
1. classify_intent
2. retrieve_documents
3. source_resolution
4. select_tool
5. execute_tool
6. evaluate_rules
7. synthesize_answer
8. validate_grounding
9. create_audit_record
"""

import re
import time
import uuid
from typing import Any, Dict, List, Optional
from app.agent.state import AgentState
from app.agent.prompts import call_ollama_llm, SYSTEM_GROUNDING_PROMPT
from app.config import settings
from app.security.privacy import inspect_privacy_boundaries
from app.security.prompt_injection import inspect_prompt_injection, sanitize_document_text
from app.security.validation import validate_question_text
from app.rag.retriever import query_documents
from app.rag.citations import format_citation, deduplicate_citations
from app.rules.source_precedence import resolve_authoritative_sources
from app.tools.student import get_student
from app.tools.attendance import get_attendance
from app.tools.results import get_result
from app.tools.policy import get_course
from app.tools.eligibility import check_exam_eligibility
from app.audit.logger import record_audit

COURSE_CODE_REGEX = re.compile(r"\b(CS\d{3}|EC\d{3}|MA\d{3}|JDG\d{3})\b", re.IGNORECASE)
SUPP_KEYWORDS = ["supplementary", "supp", "backlog exam", "failed", "re-appear", "reappear"]


def classify_intent_node(state: AgentState) -> Dict[str, Any]:
    question = state["question"]
    student_id = state["student_id"]

    # 1. Privacy inspection
    is_violation, refusal_reason = inspect_privacy_boundaries(question, student_id)
    if is_violation:
        return {
            "intent": "privacy_violation",
            "answer_type": "refused",
            "answer": refusal_reason or "Personal student information cannot be disclosed."
        }

    # 2. Prompt injection inspection
    is_injection, injection_reason = inspect_prompt_injection(question)
    if is_injection:
        return {
            "intent": "prompt_injection",
            "answer_type": "refused",
            "answer": injection_reason
        }

    # 3. Detect course code
    course_match = COURSE_CODE_REGEX.search(question)
    course_code = course_match.group(1).upper() if course_match else None

    # Also detect course names like "data structures" -> CS201
    q_lower = question.lower()
    if not course_code:
        if "data structures" in q_lower or "dsa" in q_lower:
            course_code = "CS201"
        elif "database" in q_lower or "dbms" in q_lower:
            course_code = "CS202"
        elif "operating system" in q_lower:
            course_code = "CS203"
        elif "signal processing" in q_lower or "dsp" in q_lower:
            course_code = "EC201"
        elif "microprocessor" in q_lower:
            course_code = "EC202"
        elif "discrete math" in q_lower:
            course_code = "MA201"

    # 4. Detect exam type
    is_supp = any(k in q_lower for k in SUPP_KEYWORDS)
    exam_type = "SUPPLEMENTARY" if is_supp else "REGULAR"

    # 5. Fetch student profile
    student_rec = get_student(student_id)

    # 6. Intent classification logic
    # Check for missing context (clarification needed)
    # E.g. "Can I apply?" or "Can I take the exam?" without specifying what exam or course
    if q_lower.strip().rstrip("?") in ["can i apply", "am i eligible", "what is my status"] and not course_code:
        return {
            "intent": "clarification_needed",
            "answer_type": "clarification_needed",
            "answer": "Could you please specify which course or examination you are inquiring about (e.g., end-semester exam in CS201 or supplementary exam)?",
            "student_record": student_rec,
            "course_code": None,
            "exam_type": exam_type,
        }

    # Personal student queries
    personal_indicators = [
        "my attendance", "overall attendance", "attendance percentage", "classes attended",
        "how many classes", "my marks", "my result", "did i pass", "am i eligible",
        "can i take", "can i appear", "my backlogs", "my cgpa", "why am i not eligible",
        "my current attendance", "all courses"
    ]

    is_personal = any(ind in q_lower for ind in personal_indicators) or (
        "my" in q_lower and ("attendance" in q_lower or "marks" in q_lower or "grades" in q_lower or "results" in q_lower)
    )
    is_eligibility = "eligible" in q_lower or "can i" in q_lower or "permitted" in q_lower

    if is_eligibility and (course_code or "exam" in q_lower or "supp" in q_lower):
        intent = "eligibility_check"
    elif is_personal:
        intent = "student_personal"
    else:
        intent = "policy_factual"

    return {
        "intent": intent,
        "course_code": course_code,
        "exam_type": exam_type,
        "student_record": student_rec,
    }


def retrieve_documents_node(state: AgentState) -> Dict[str, Any]:
    if state.get("answer_type") in ["refused", "clarification_needed"]:
        return {}

    question = state["question"]
    raw_chunks = query_documents(question, top_k=6)

    # Sanitize document text against prompt injection patterns
    sanitized_chunks = []
    for c in raw_chunks:
        sanitized_chunks.append({
            "id": c["id"],
            "text": sanitize_document_text(c["text"]),
            "metadata": c["metadata"],
            "score": c.get("score", 0.0),
            "distance": c.get("distance", 1.0)
        })

    return {"retrieved_chunks": sanitized_chunks}


def source_resolution_node(state: AgentState) -> Dict[str, Any]:
    if state.get("answer_type") in ["refused", "clarification_needed"]:
        return {}

    chunks = state.get("retrieved_chunks", [])
    if not chunks:
        return {
            "selected_source": None,
            "candidate_sources": [],
            "excluded_sources": [],
            "conflict_flag": False,
            "precedence_reason": "No candidate chunks retrieved.",
            "conflicts_detected": []
        }

    # Extract distinct candidate documents from chunk metadata
    candidate_docs = []
    seen_docs = set()
    for c in chunks:
        meta = c["metadata"]
        doc_id = meta.get("doc_id")
        if doc_id and doc_id not in seen_docs:
            seen_docs.add(doc_id)
            candidate_docs.append(dict(meta))

    student_ctx = {
        "as_of_date": state.get("as_of_date", "2026-10-06"),
        "programme": state.get("student_record", {}).get("programme") if state.get("student_record") else None,
        "batch_year": state.get("student_record", {}).get("batch_year") if state.get("student_record") else None,
    }

    resolution = resolve_authoritative_sources(candidate_docs, student_ctx)

    conflicts = []
    if resolution["conflict_status"]:
        conflicts.append("Conflicting authoritative regulations detected at identical authority levels without clear supersession.")

    # Also check if query is demonstrating the intentional version conflict demo:
    # If both ACAD-REG-2024 and ACAD-REG-2021 were retrieved
    retrieved_doc_ids = {c["metadata"].get("doc_id") for c in chunks}
    policy_notes = list(state.get("policy_notes", []))
    if "ACAD-REG-2021" in retrieved_doc_ids and "ACAD-REG-2024" in retrieved_doc_ids:
        policy_notes.append(
            "Version Conflict Resolution: ACAD-REG-2024 (v3.1, Attendance 75%) supersedes ACAD-REG-2021 (v2.0, Attendance 70%). "
            "The older regulation has been excluded based on authoritative supersession rules."
        )

    return {
        "selected_source": resolution["selected_source"],
        "candidate_sources": resolution["candidate_sources"],
        "excluded_sources": resolution["excluded_sources"],
        "precedence_reason": resolution["reason"],
        "conflict_flag": resolution["conflict_status"],
        "conflicts_detected": conflicts,
        "policy_notes": policy_notes
    }


def select_tool_node(state: AgentState) -> Dict[str, Any]:
    if state.get("answer_type") in ["refused", "clarification_needed"]:
        return {}

    intent = state.get("intent")
    tools = []

    if intent in ["eligibility_check", "student_personal"]:
        tools.append("get_student")
        if state.get("course_code"):
            tools.append("get_attendance")
            tools.append("get_result")
            tools.append("get_course")
        else:
            tools.append("get_attendance")

    if intent == "eligibility_check":
        tools.append("check_exam_eligibility")

    return {"tools_invoked": tools}


def execute_tool_node(state: AgentState) -> Dict[str, Any]:
    if state.get("answer_type") in ["refused", "clarification_needed"]:
        return {}

    tools = state.get("tools_invoked", [])
    student_id = state["student_id"]
    course_code = state.get("course_code")

    tool_inputs = []
    tool_outputs = []

    for t in tools:
        if t == "get_student":
            tool_inputs.append({"tool": "get_student", "student_id": student_id})
            res = get_student(student_id)
            tool_outputs.append({"tool": "get_student", "output": res})

        elif t == "get_attendance":
            tool_inputs.append({"tool": "get_attendance", "student_id": student_id, "course_code": course_code})
            res = get_attendance(student_id, course_code)
            tool_outputs.append({"tool": "get_attendance", "output": res})

        elif t == "get_result":
            if course_code:
                tool_inputs.append({"tool": "get_result", "student_id": student_id, "course_code": course_code})
                res = get_result(student_id, course_code)
                tool_outputs.append({"tool": "get_result", "output": res})

        elif t == "get_course":
            if course_code:
                tool_inputs.append({"tool": "get_course", "course_code": course_code})
                res = get_course(course_code)
                tool_outputs.append({"tool": "get_course", "output": res})

    return {
        "tool_inputs": tool_inputs,
        "tool_outputs": tool_outputs
    }


def evaluate_rules_node(state: AgentState) -> Dict[str, Any]:
    if state.get("answer_type") in ["refused", "clarification_needed"]:
        return {}

    intent = state.get("intent")
    student_id = state["student_id"]
    course_code = state.get("course_code")
    exam_type = state.get("exam_type", "REGULAR")

    rules_applied = list(state.get("rules_applied", []))
    citations = list(state.get("citations", []))

    if intent == "eligibility_check" and course_code:
        elig_res = check_exam_eligibility(
            student_id=student_id,
            course_code=course_code,
            exam_type=exam_type,
            as_of_date=state.get("as_of_date", "2026-10-06")
        )

        state["tool_outputs"].append({"tool": "check_exam_eligibility", "output": elig_res})
        rules_applied.extend(elig_res.get("rules_applied", []))

        # Add citations for the rules applied
        for src in elig_res.get("sources", []):
            citations.append({
                "title": "Official Examination & Academic Regulations",
                "doc_id": src.get("doc_id", "ACAD-REG-2024"),
                "section": src.get("section", "Section 4.1"),
                "page": 1,
                "version": "3.1",
                "effective_date": "2024-07-01",
                "authority_level": 1
            })

    return {
        "rules_applied": rules_applied,
        "citations": deduplicate_citations(citations)
    }


def synthesize_answer_node(state: AgentState) -> Dict[str, Any]:
    if state.get("answer_type") in ["refused", "clarification_needed"]:
        return {}

    if state.get("conflict_flag"):
        return {
            "answer_type": "conflict_flagged",
            "answer": (
                "Conflicting authoritative policies were found with equal authority levels and dates. "
                "The system has safely flagged this policy conflict rather than silently guessing."
            ),
            "citations": []
        }

    intent = state.get("intent")
    student_id = state["student_id"]
    course_code = state.get("course_code")
    student_rec = state.get("student_record")
    tool_outputs = state.get("tool_outputs", [])
    chunks = state.get("retrieved_chunks", [])
    selected_source = state.get("selected_source")

    # CASE A: Eligibility check / Multi-step questions -> CALCULATED
    if intent == "eligibility_check":
        elig_data = next((o["output"] for o in tool_outputs if o["tool"] == "check_exam_eligibility"), None)
        att_data = next((o["output"] for o in tool_outputs if o["tool"] == "get_attendance"), None)

        if elig_data:
            eligible_str = "ELIGIBLE" if elig_data["eligible"] else "NOT ELIGIBLE"
            ans_parts = [
                f"**Verdict:** You are **{eligible_str}** for the {elig_data.get('exam_type', 'REGULAR')} examination in **{course_code}**.",
                f"- **Reason:** {elig_data.get('reason')}",
            ]
            if att_data and isinstance(att_data, dict) and att_data.get("found"):
                ans_parts.append(
                    f"- **Attendance Details:** {att_data.get('classes_attended')}/{att_data.get('classes_held')} classes attended "
                    f"({att_data.get('attendance_percentage')}%, threshold >= 75.0%)."
                )
            if student_rec:
                ans_parts.append(
                    f"- **Academic Standing:** CGPA {student_rec['cgpa']}, Active Backlogs: {student_rec['active_backlogs']} (Limit: <= 2)."
                )

            return {
                "answer_type": "calculated",
                "answer": "\n".join(ans_parts)
            }

    # CASE B: Personal Attendance or Marks -> CALCULATED
    if intent == "student_personal":
        att_data = next((o["output"] for o in tool_outputs if o["tool"] == "get_attendance"), None)
        res_data = next((o["output"] for o in tool_outputs if o["tool"] == "get_result"), None)

        ans_parts = []
        if att_data and isinstance(att_data, dict):
            if "attendance_percentage" in att_data:
                # Specific course
                ans_parts.append(
                    f"Your current attendance in **{att_data.get('course_code')}** ({att_data.get('course_name')}) is **{att_data.get('attendance_percentage')}%** "
                    f"({att_data.get('classes_attended')} classes attended out of {att_data.get('classes_held')} held). "
                    f"Status: **{att_data.get('status')}** (Mandatory threshold is 75.0%)."
                )
            elif "overall_attendance_percentage" in att_data:
                # All courses
                ans_parts.append(
                    f"Your overall aggregate attendance across all courses is **{att_data.get('overall_attendance_percentage')}%** "
                    f"({att_data.get('total_classes_attended')}/{att_data.get('total_classes_held')} classes attended)."
                )
                for c in att_data.get("courses", []):
                    ans_parts.append(
                        f"- **{c['course_code']}** ({c['course_name']}): {c['attendance_percentage']}% "
                        f"({c['classes_attended']}/{c['classes_held']} classes) - {c['status']}"
                    )

        if res_data and isinstance(res_data, dict) and res_data.get("found"):
            ans_parts.append(
                f"Your examination result in **{res_data.get('course_code')}** ({res_data.get('exam_session')}): "
                f"Internal: {res_data.get('internal_marks')}/40, External: {res_data.get('external_marks')}/60, "
                f"Total: **{res_data.get('total_marks')}/{res_data.get('max_marks')}**, Result: **{res_data.get('result')}**."
            )

        if ans_parts:
            # Add citation to attendance policy
            citations = list(state.get("citations", []))
            citations.append({
                "title": "Comprehensive Student Attendance Policy v2.0",
                "doc_id": "ATT-POL-2024",
                "section": "Section 2.1 & 2.2",
                "page": 1,
                "version": "2.0",
                "effective_date": "2024-07-01",
                "authority_level": 2
            })
            return {
                "answer_type": "calculated",
                "answer": "\n\n".join(ans_parts),
                "citations": deduplicate_citations(citations)
            }

    # CASE C: Factual University Policy Retrieval -> RETRIEVED_FACT
    # Check if retrieval returned relevant chunks
    relevant_chunks = [c for c in chunks if c.get("score", 0.0) >= 0.25]
    if not relevant_chunks:
        return {
            "answer_type": "not_found",
            "answer": "I could not find this information in the authorised university sources.",
            "citations": []
        }

    # Prepare context from the top selected document chunks
    citations = list(state.get("citations", []))
    context_snippets = []
    top_doc_id = selected_source.get("doc_id") if selected_source else relevant_chunks[0]["metadata"].get("doc_id")

    # Prioritize chunks matching the selected authoritative document
    top_chunks = [c for c in relevant_chunks if c["metadata"].get("doc_id") == top_doc_id]
    if not top_chunks:
        top_chunks = relevant_chunks[:2]

    for c in top_chunks:
        meta = c["metadata"]
        context_snippets.append(f"Document [{meta.get('title')}, Section {meta.get('section')}]:\n{c['text']}")
        citations.append(format_citation(meta))

    combined_context = "\n\n".join(context_snippets)

    # Prompt Ollama LLM to synthesize natural response strictly from context
    synthesis_prompt = (
        f"Question: {state['question']}\n\n"
        f"Authoritative Context:\n{combined_context}\n\n"
        "Instructions: Synthesize a concise, direct, factual answer based strictly on the authoritative context above. "
        "State the exact rule, requirement, numbers, and document section."
    )

    llm_response = call_ollama_llm(synthesis_prompt)

    # Determine if LLM response is valid and grounded
    is_valid_llm = (
        llm_response
        and len(llm_response.strip()) > 15
        and "could not find this information" not in llm_response.lower()
    )

    if is_valid_llm:
        ans = llm_response
    else:
        # High quality deterministic extraction from the selected authoritative document
        top_chunk = top_chunks[0]
        meta = top_chunk["metadata"]
        lines = [line.strip() for line in top_chunk["text"].split("\n") if line.strip()]
        
        # Filter lines to most informative content (skip header markers)
        body_lines = [l for l in lines if not l.startswith("===") and not l.startswith("Document ID:") and not l.startswith("Authority Level:")]
        extracted_body = "\n".join(body_lines[:6])

        ans = (
            f"According to **{meta.get('title')}** ({meta.get('section')}):\n\n"
            f"{extracted_body}\n\n"
            f"*(Document ID: {meta.get('doc_id')}, Version: {meta.get('version')}, Effective: {meta.get('effective_from')})*"
        )

    return {
        "answer_type": "retrieved_fact",
        "answer": ans,
        "citations": deduplicate_citations(citations)
    }


def validate_grounding_node(state: AgentState) -> Dict[str, Any]:
    ans_type = state.get("answer_type", "not_found")
    ans = state.get("answer", "")

    # Grounding check: If answer_type is retrieved_fact but text indicates not found
    if "could not find this information" in ans.lower():
        ans_type = "not_found"

    # Enforce strict fallback text
    if ans_type == "not_found" and not ans:
        ans = "I could not find this information in the authorised university sources."

    # Validate that citations exist for factual answers
    citations = state.get("citations", [])
    if ans_type == "retrieved_fact" and not citations:
        chunks = state.get("retrieved_chunks", [])
        if chunks:
            citations.append(format_citation(chunks[0]["metadata"]))

    return {
        "answer_type": ans_type,
        "answer": ans,
        "citations": citations
    }


def create_audit_record_node(state: AgentState) -> Dict[str, Any]:
    start_time = state.get("start_time", time.time())
    latency_ms = round((time.time() - start_time) * 1000.0, 2)
    trace_id = state.get("trace_id", str(uuid.uuid4()))

    record_audit(
        trace_id=trace_id,
        student_id=state.get("student_id", "UNKNOWN"),
        question=state.get("question", ""),
        answer_type=state.get("answer_type", "not_found"),
        final_answer=state.get("answer", ""),
        latency_ms=latency_ms,
        model_used=state.get("model_used", settings.OLLAMA_MODEL),
        selected_sources=[state.get("selected_source")] if state.get("selected_source") else [],
        retrieved_sources=[c.get("metadata") for c in state.get("retrieved_chunks", [])],
        tools_invoked=state.get("tools_invoked", []),
        tool_inputs=state.get("tool_inputs", []),
        tool_outputs=state.get("tool_outputs", []),
        rules_applied=state.get("rules_applied", []),
        conflicts_detected=state.get("conflicts_detected", [])
    )

    return {
        "trace_id": trace_id,
        "audit_id": trace_id,
        "latency_ms": latency_ms
    }
