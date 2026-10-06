"""
Document retrieval node for LangGraph pipeline.
Retrieves semantic chunks from ChromaDB and sanitizes against prompt injection.
"""

from typing import Any, Dict
from app.agent.state import AgentState
from app.core.security import sanitize_document_text
from app.rag.retriever import query_documents


def retrieve_documents_node(state: AgentState) -> Dict[str, Any]:
    if state.get("answer_type") in ["refused", "clarification_needed"]:
        return {}

    question = state["question"]
    top_k = state.get("top_k") or 5
    raw_chunks = query_documents(question, top_k=top_k)

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
