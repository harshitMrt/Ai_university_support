"""
Document parsing and section-aware chunking pipeline.
Ensures no metadata is lost and each chunk retains full provenance and section context.
"""

import re
from pathlib import Path
from typing import Any, Dict, List
import pypdf
import docx


def extract_text_from_file(file_path: Path) -> str:
    suffix = file_path.suffix.lower()
    if suffix in [".txt", ".md"]:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            return f.read()
    elif suffix == ".pdf":
        text_parts = []
        reader = pypdf.PdfReader(str(file_path))
        for page_idx, page in enumerate(reader.pages):
            page_text = page.extract_text() or ""
            text_parts.append(f"\n[PAGE {page_idx + 1}]\n" + page_text)
        return "\n".join(text_parts)
    elif suffix in [".docx", ".doc"]:
        doc = docx.Document(str(file_path))
        return "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
    else:
        # Fallback raw read
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            return f.read()


def chunk_document(
    text: str,
    base_metadata: Dict[str, Any],
    chunk_size: int = 500,
    chunk_overlap: int = 80
) -> List[Dict[str, Any]]:
    """
    Chunks document text by sections when possible, preserving all rich metadata.
    """
    chunks = []
    lines = text.split("\n")

    current_section = "General / Preamble"
    current_page = 1
    current_buffer: List[str] = []
    current_char_count = 0

    section_pattern = re.compile(r"^(SECTION\s+\d+[^:\n]*:?[^\n]*|CHAPTER\s+\d+[^:\n]*:?[^\n]*)", re.IGNORECASE)
    page_pattern = re.compile(r"^\[PAGE\s+(\d+)\]", re.IGNORECASE)

    chunk_idx = 0

    def flush_buffer(section_name: str, page_num: int):
        nonlocal chunk_idx, current_buffer, current_char_count
        if not current_buffer:
            return
        chunk_text = "\n".join(current_buffer).strip()
        if not chunk_text:
            return

        chunk_id = f"{base_metadata.get('doc_id', 'DOC')}-chunk-{chunk_idx}"
        chunk_metadata = dict(base_metadata)
        chunk_metadata["chunk_id"] = chunk_id
        chunk_metadata["section"] = section_name
        chunk_metadata["page"] = page_num
        chunk_metadata["chunk_index"] = chunk_idx

        # Ensure all required metadata fields exist as strings/numbers for ChromaDB
        for key in [
            "doc_id", "title", "issuer", "authority_level", "doc_type",
            "version", "effective_from", "effective_to", "supersedes",
            "scope_programmes", "scope_batches", "provenance", "retrieved_on", "synthetic"
        ]:
            val = chunk_metadata.get(key)
            if val is None:
                chunk_metadata[key] = ""
            elif isinstance(val, (int, float, bool)):
                chunk_metadata[key] = val
            else:
                chunk_metadata[key] = str(val)

        chunks.append({
            "id": chunk_id,
            "text": chunk_text,
            "metadata": chunk_metadata
        })
        chunk_idx += 1
        current_buffer = []
        current_char_count = 0

    for line in lines:
        page_match = page_pattern.match(line.strip())
        if page_match:
            try:
                current_page = int(page_match.group(1))
            except ValueError:
                pass
            continue

        sec_match = section_pattern.match(line.strip())
        if sec_match:
            # New section encountered
            if current_buffer:
                flush_buffer(current_section, current_page)
            current_section = sec_match.group(1).strip()
            current_buffer.append(line)
            current_char_count += len(line)
            continue

        current_buffer.append(line)
        current_char_count += len(line)

        if current_char_count >= chunk_size:
            flush_buffer(current_section, current_page)

    flush_buffer(current_section, current_page)
    return chunks
