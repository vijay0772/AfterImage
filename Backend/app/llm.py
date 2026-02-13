# app/llm.py
"""LLM layer: answer from candidate lines, return evidence_line_ids."""

import json
from openai import OpenAI
from .config import settings

client = OpenAI(api_key=settings.openai_api_key)

SYSTEM = """You answer questions ONLY using the provided candidate lines from the document.

Rules:
- You MUST select evidence ONLY from the provided lines. Each line has a line_id (e.g., p5_b12_l3).
- Return evidence_line_ids: an array of line_id strings that support your answer.
- Do NOT fabricate or invent line_ids. Only use IDs from the CANDIDATE LINES section.
- If the answer is not supported by the candidate lines, return:
  {"answer":"Not found in document","evidence_line_ids":[]}
- If a specific date is mentioned in the question (e.g. April 6, 04/06/24), ONLY select evidence lines that contain that date. Do not select lines with a different date.
- Do NOT select lines with garbled/corrupted names (random caps, 4+ consecutive consonants, encoding artifacts). Prefer lines with clear readable names (e.g. "Ordering Doctor: [Name]" or clean "Signed by [Name]" lines). If all candidate lines appear garbled, return "Not found in document".
- Return STRICT JSON with keys: answer (string), evidence_line_ids (array of strings).
- Include up to 5 evidence_line_ids when multiple signers or sources match (e.g. multiple signers on the same date).
- Your answer must be grounded in the cited lines. Do not make unsupported claims.
"""


def _parse_llm_output(out_text: str) -> dict:
    default = {"answer": "Not found in document", "evidence_line_ids": []}
    if not out_text or not out_text.strip():
        return default
    try:
        data = json.loads(out_text.strip())
    except json.JSONDecodeError:
        start, end = out_text.find("{"), out_text.rfind("}")
        if start >= 0 and end > start:
            try:
                data = json.loads(out_text[start : end + 1])
            except json.JSONDecodeError:
                return default
        else:
            return default
    if "answer" not in data or not isinstance(data.get("answer"), str):
        data["answer"] = "Not found in document"
    ids = data.get("evidence_line_ids", [])
    if not isinstance(ids, list):
        ids = []
    data["evidence_line_ids"] = [str(x).strip() for x in ids[:5] if x]
    if (data.get("answer") or "").lower().startswith("not found"):
        data["evidence_line_ids"] = []
    return data


def ask_llm(question: str, candidate_lines: list[dict], question_date: str | None = None) -> dict:
    """
    Ask LLM to answer from candidate lines. Candidate lines must have line_id and text.
    question_date: if extracted from question, reinforces date constraint in prompt.
    Returns: {answer, evidence_line_ids}
    """
    if not candidate_lines:
        return {"answer": "Not found in document", "evidence_line_ids": []}
    # Format: line_id | page N | text
    lines_text = "\n".join(
        f"{ln['line_id']} | page {ln['page']} | {ln['text']}"
        for ln in candidate_lines
    )
    date_hint = ""
    if question_date:
        date_hint = f"\n\nIMPORTANT: The question mentions date {question_date}. Only select lines containing this date. Ignore lines with other dates.\n"
    user_prompt = (
        f"Question: {question}\n\n"
        "CANDIDATE LINES (select evidence_line_ids ONLY from these):\n"
        f"{lines_text}\n"
        f"{date_hint}\n"
        "Return JSON: {\"answer\": \"...\", \"evidence_line_ids\": [\"p1_b0_l0\", ...]}"
    )
    try:
        resp = client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": SYSTEM},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0,
            response_format={"type": "json_object"},
        )
        out_text = (resp.choices[0].message.content or "").strip()
        return _parse_llm_output(out_text)
    except Exception:
        return {"answer": "Not found in document", "evidence_line_ids": []}
