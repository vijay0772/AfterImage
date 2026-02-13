# chunk.py
"""Chunk extraction with overlap for better retrieval alignment."""

import re

def normalize(s: str) -> str:
    s = s.replace("\u00a0", " ")
    s = re.sub(r"\s+", " ", s).strip()
    return s

# Smaller chunks with overlap so chunks better align with sentences/paragraphs
CHUNK_LINES = 5
OVERLAP_LINES = 2

def make_chunks(extracted: dict) -> list[dict]:
    chunks = []
    chunk_id = 0
    for p in extracted["pages"]:
        lines = [ln.strip() for ln in p["text"].splitlines() if ln.strip()]
        i = 0
        while i < len(lines):
            block = lines[i : i + CHUNK_LINES]
            if block:
                chunk_id += 1
                chunks.append({
                    "chunk_id": chunk_id,
                    "page": p["page"],
                    "text": normalize("\n".join(block))
                })
            # overlap: step forward by (CHUNK_LINES - OVERLAP_LINES)
            i += max(1, CHUNK_LINES - OVERLAP_LINES)
    return chunks
