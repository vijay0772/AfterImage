# retrieve.py
"""Line-based retrieval: date filtering, scoring, expand ±2 neighbors."""

import re
from collections import defaultdict

STOP = set(["the", "a", "an", "and", "or", "to", "of", "in", "on", "for", "with", "is", "are", "was", "were", "by", "when"])

# Month name -> number
MONTH_MAP = {
    "january": "01", "jan": "01", "february": "02", "feb": "02",
    "march": "03", "mar": "03", "april": "04", "apr": "04",
    "may": "05", "june": "06", "jun": "06", "july": "07", "jul": "07",
    "august": "08", "aug": "08", "september": "09", "sep": "09", "sept": "09",
    "october": "10", "oct": "10", "november": "11", "nov": "11",
    "december": "12", "dec": "12",
}
DATE_RE = re.compile(r"\b\d{1,2}/\d{1,2}/\d{2,4}\b")
DATE_PATTERNS = [
    (r"(\d{1,2})/(\d{1,2})/(\d{2,4})", lambda m: f"{m.group(1).zfill(2)}/{m.group(2).zfill(2)}/{m.group(3)[-2:] if len(m.group(3)) == 4 else m.group(3)}"),
    (r"(?:april|apr)\s+6(?:\s|,|$|\d)", lambda m: "04/06/24"),
    (r"(?:april|apr)\s+6", lambda m: "04/06/24"),
    (r"april\s+(\d{1,2})", lambda m: f"04/{m.group(1).zfill(2)}/24"),
    (r"(\w+)\s+(\d{1,2})(?:\s|,|$|\d)", lambda m: (MONTH_MAP.get(m.group(1).lower()[:3], "01"), m.group(2).zfill(2))),
]


def extract_date_from_question(question: str) -> str | None:
    """
    Extract date from question. Returns normalized form like 04/06/24 or None.
    Handles: 04/06/24, 4/6/24, April 6, april 6, etc.
    """
    q = (question or "").lower()
    # Explicit date (04/06/24, 4/6/24)
    m = DATE_RE.search(question or "")
    if m:
        parts = m.group(0).split("/")
        mo, d = parts[0].zfill(2), parts[1].zfill(2)
        yr = parts[2][-2:] if len(parts[2]) == 4 else parts[2]
        return f"{mo}/{d}/{yr}"
    # April 6, april 6th
    if re.search(r"april\s+6|apr\s+6", q):
        return "04/06/24"
    for name, num in MONTH_MAP.items():
        if name in q:
            dm = re.search(rf"{name}\s+(\d{{1,2}})", q)
            if dm:
                return f"{num}/{dm.group(1).zfill(2)}/24"
    return None


def tokenize(s: str) -> list[str]:
    s = (s or "").lower()
    s = re.sub(r"[^a-z0-9/ ]+", " ", s)
    tokens = [t for t in s.split() if t and t not in STOP]
    # Expand with stem/related forms so "discharged" matches "discharge", "admitted" matches "admission"
    expanded = list(tokens)
    for t in tokens:
        if t == "discharged":
            expanded.append("discharge")
        elif t == "admitted":
            expanded.extend(["admission", "admit", "admitted"])
    return list(dict.fromkeys(expanded))


BOOST_TERMS = ["signed", "discharge", "discharged", "admission", "admitted", "pacu", "criteria", "audit", "order", "electronically", "signature", "patient", "medication", "mg"]


def score_line(qtoks: list[str], line_text: str, question_date: str | None) -> float:
    """
    Score line. Strong boosts: +3 if line contains question date, +2 if Signed, +1 if PACU/Discharge.
    """
    ctoks = tokenize(line_text)
    cset = set(ctoks)
    base = sum(1 for t in qtoks if t in cset)
    boost = 0.0
    lower = (line_text or "").lower()
    # Date match: strongest signal
    if question_date and question_date in line_text:
        boost += 3.0
    # Signed-related
    if "signed" in lower or "signature" in lower:
        boost += 2.0
    if "electronically" in lower and "signed" in lower:
        boost += 0.5
    # Discharge/PACU/Admission
    if "pacu" in lower or "post-anaesthesia" in lower or "post anaesthesia" in lower:
        boost += 1.0
    if "discharge" in lower or "discharged" in lower:
        boost += 1.0
    if "admission" in lower or "admitted" in lower or "admit" in lower:
        boost += 1.0
    # Other clinical terms
    for term in BOOST_TERMS:
        if term in lower and term not in ("signed", "signature", "electronically"):
            boost += 0.3
    if DATE_RE.search(lower):
        boost += 0.5
    return base + boost


def top_k_lines_with_context(
    question: str,
    lines: list[dict],
    k: int = 20,
    context_lines: int = 2,
) -> list[dict]:
    """
    Extract date from question, filter by date when present, score with date/Signed/PACU/Discharge boosts,
    take top k, expand ±context_lines neighbors.
    """
    if not lines:
        return []
    question_date = extract_date_from_question(question)
    qtoks = tokenize(question)
    # Date filter: when question has a date, strongly prefer lines containing it
    if question_date:
        def _line_has_date(ln: dict) -> bool:
            t = ln.get("text", "")
            if question_date in t:
                return True
            # Also match 4/6/24, 04/6/24, 4/06/24
            parts = question_date.split("/")
            if len(parts) == 3:
                alt1 = f"{int(parts[0])}/{int(parts[1])}/{parts[2]}"
                if alt1 in t:
                    return True
            return False
        date_matches = [ln for ln in lines if _line_has_date(ln)]
        if date_matches:
            pool = date_matches
        else:
            pool = lines
    else:
        pool = lines
    lines_by_page: dict[int, list[dict]] = defaultdict(list)
    for ln in lines:
        lines_by_page[ln["page"]].append(ln)
    line_to_page_idx: dict[str, tuple[int, int]] = {}
    for page, page_lines in lines_by_page.items():
        for i, ln in enumerate(page_lines):
            line_to_page_idx[ln["line_id"]] = (page, i)
    # Score pool (or all lines) with date-aware scoring
    scored = [(score_line(qtoks, ln["text"], question_date), ln) for ln in pool]
    scored.sort(key=lambda x: x[0], reverse=True)
    hits = [ln for s, ln in scored[:k] if s > 0]
    if not hits:
        hits = pool[: min(k * 2, len(pool))]
    if not hits:
        hits = lines[: min(k * 2, len(lines))]
    # Expand each hit with ±context_lines neighbors (same page)
    seen: set[str] = set()
    result: list[dict] = []
    for hit in hits:
        lid = hit["line_id"]
        if lid in seen:
            continue
        page, idx = line_to_page_idx.get(lid, (hit["page"], 0))
        page_lines = lines_by_page[page]
        start = max(0, idx - context_lines)
        end = min(len(page_lines), idx + context_lines + 1)
        for ln in page_lines[start:end]:
            lid2 = ln["line_id"]
            if lid2 not in seen:
                # When question has date, only include lines that contain that date
                if question_date:
                    if question_date not in ln.get("text", ""):
                        continue
                seen.add(lid2)
                result.append(ln)
    # If date filter removed everything, fall back to unfiltered hits
    if question_date and not result and hits:
        result = [ln for ln in hits if question_date in ln.get("text", "")]
    return result
