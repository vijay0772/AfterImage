# flowsheet.py
"""Flowsheet-aware extraction and retrieval for clinical vitals pages (e.g. pages 6-7)."""

import logging
import re
from collections import Counter, defaultdict

logger = logging.getLogger(__name__)

# Patterns for flowsheet detection (OCR-tolerant: Activit;i, Date: on separate line, etc.)
ACTIVITY_DATE_RE = re.compile(
    r"(?:Activity|Activit[\w:\s']*)\s*Date:\s*(\d{1,2}/\d{1,2}/\d{2,4})|"
    r"Date:\s*(\d{1,2}/\d{1,2}/\d{2,4})\b",
    re.IGNORECASE,
)
TIME_RE = re.compile(r"Time:\s*(\d{1,4})(?::(\d{2}))?", re.IGNORECASE)
CONTINUED_RE = re.compile(r"\(continued\)", re.IGNORECASE)
FLOWSHEET_MARKERS = [
    r"Activity\s+Date:",
    r"Clinical\s+Monitor\s+Interface",
    r"Frequent\s+Neuro\s+Checks",
    r"Pulse\s*:",
    r"Respiratory\s+rate\s*:",
    r"Blood\s+pressure\s*:",
    r"Blood\s+\d",
    r"SP0?2\s*%?\s*:",
    r"Mean\s+arterial\s+pressure",
    r"MAP\s*:",
    r"GCS\s*:",
    r"Glasgow",
]
FLOWSHEET_MARKER_RE = re.compile("|".join(f"({p})" for p in FLOWSHEET_MARKERS), re.IGNORECASE)
SKIP_RE = re.compile(r"See\s+next\s+(page|12a9e|12age|\.\.\.)?", re.IGNORECASE)

VITALS_KEYWORDS = [
    "pulse", "respiratory rate", "blood pressure", "blood", "bp", "spo2", "sp02", "map",
    "mean arterial pressure", "level of consciousness", "loc", "gcs", "glasgow",
    "pupil", "neuro", "heart rate", "resp", "o2", "oxygen",
]

TIME_PATTERN_RE = re.compile(r"(?:^|[\s,])(\d{1,2}):?(\d{2})\b|\b(\d{3,4})\b")


def _norm_time(t: str) -> str:
    """Normalize time to HHMM (4 digits). 21:30 -> 2130, 2130 -> 2130."""
    t = (t or "").strip().replace(":", "")
    if len(t) == 3:
        t = "0" + t
    return t if len(t) == 4 else ""


def _norm_date(d: str) -> str:
    """Normalize date to MM/DD/YY."""
    if not d:
        return ""
    parts = re.findall(r"\d+", d)
    if len(parts) >= 3:
        mo, day = parts[0].zfill(2), parts[1].zfill(2)
        yr = parts[2][-2:] if len(parts[2]) >= 2 else parts[2]
        return f"{mo}/{day}/{yr}"
    return d


def _normalize_text(text: str) -> str:
    """Lowercase, collapse whitespace, apply OCR variant fixes."""
    if not text:
        return ""
    t = re.sub(r"\s+", " ", (text or "").lower().strip())
    t = re.sub(r"sp02|sp0\s*2", "spo2", t)
    t = re.sub(r"activitv|activit\s*:\s*i", "activity", t)
    t = re.sub(r"respi\s*r|respi\s*[i1·]\s*ato[r\s]*[i1·]\s*", "respiratory ", t)
    t = re.sub(r"arte[1•]\s*ial|arte\s*[i1·]\s*al", "arterial", t)
    t = re.sub(r"pressu[i1·]\s*e", "pressure", t)
    t = re.sub(r"i\s*·\s*ate", "rate", t)
    return t


def _is_skip_line(text: str) -> bool:
    if not text or not text.strip():
        return True
    t = text.strip().lower()
    if SKIP_RE.search(t):
        return True
    if re.match(r"^\(continued\)\s*$|^continued\s*$", t):
        return True
    if t in ("---", "--", "..."):
        return True
    return False


# Field lexicon: field -> list of regex patterns
FIELD_LEXICON = {
    "blood pressure": [
        re.compile(r"\bblood\s+pressure\b", re.IGNORECASE),
        re.compile(r"\bbp\b", re.IGNORECASE),
        re.compile(r"\bblood\s+\d{2,3}/\d{2,3}\b"),  # Blood 126/61
    ],
    "pulse": [
        re.compile(r"\bpulse\b", re.IGNORECASE),
        re.compile(r"\bheart\s+rate\b", re.IGNORECASE),
    ],
    "respiratory rate": [
        re.compile(r"\brespiratory\s+rate\b", re.IGNORECASE),
        re.compile(r"respi[\w\s·]*\b(rate|ate)\b", re.IGNORECASE),
        re.compile(r"\brr\b(?!\d)"),
        re.compile(r"\bresp\b", re.IGNORECASE),
    ],
    "spo2": [
        re.compile(r"\bspo2\b", re.IGNORECASE),
        re.compile(r"\bsp02\b", re.IGNORECASE),
        re.compile(r"sp0?2\s*%?\s*[:=]?\s*\d{2,3}", re.IGNORECASE),
        re.compile(r"\bo2\s*%?\s*[:=]?\s*\d{2,3}", re.IGNORECASE),
    ],
    "mean arterial pressure": [
        re.compile(r"\bmean\s+arterial\s+pressure\b", re.IGNORECASE),
        re.compile(r"mean\s+arte[r1•\s·]*ial\s+pressu[r1•\s·]*e", re.IGNORECASE),
        re.compile(r"\bmap\b", re.IGNORECASE),
        re.compile(r"map\s*[:=]?\s*\d{2,3}", re.IGNORECASE),
    ],
    "level of consciousness": [
        re.compile(r"\blevel\s+of\s+consciousness\b", re.IGNORECASE),
        re.compile(r"\bloc\b", re.IGNORECASE),
        re.compile(r"\bawake\b|\balert\b|\bconscious\b", re.IGNORECASE),
    ],
    "gcs": [
        re.compile(r"\bglasgow\b", re.IGNORECASE),
        re.compile(r"\bgcs\b", re.IGNORECASE),
    ],
    "pupil": [
        re.compile(r"\bpupil\b", re.IGNORECASE),
    ],
    "neuro": [
        re.compile(r"\bneuro\b", re.IGNORECASE),
    ],
}


def _build_logical_lines(section_lines: list[dict]) -> list[dict]:
    """Merge split table cells: 'Blood' + '126/61' -> 'Blood 126/61'."""
    result = []
    i = 0
    while i < len(section_lines):
        ln = section_lines[i]
        raw = (ln.get("text") or "").strip()
        next_raw = (section_lines[i + 1].get("text") or "").strip() if i + 1 < len(section_lines) else ""
        if re.match(r"^blood\s*$", raw, re.IGNORECASE) and re.match(r"^\d{2,3}/\d{2,3}\s*$", next_raw):
            val_ln = section_lines[i + 1]
            merged = {**ln, "text": f"Blood {next_raw}", "bbox": val_ln.get("bbox") or ln.get("bbox")}
            result.append(merged)
            i += 2
            continue
        if re.match(r"^(%?\s*)?sp0?2\s*%?\s*:?\s*$", raw, re.IGNORECASE) and (
            re.match(r"^\d{2,3}\s*%?\s*$", next_raw) or re.match(r"^:\s*\d{2,3}\s*%?\s*$", next_raw)
        ):
            val = re.sub(r"[^0-9]", "", next_raw)
            merged = {**ln, "text": f"SPO2 {val}", "bbox": section_lines[i + 1].get("bbox") or ln.get("bbox")}
            result.append(merged)
            i += 2
            continue
        result.append(ln)
        i += 1
    return result


def find_value_line(section_lines: list[dict], field: str) -> dict | None:
    """
    Find best matching line using normalization + regex lexicon.
    Handles split lines (Blood + value). Returns line dict with line_id, page, text, bbox.
    """
    logical = _build_logical_lines(section_lines)
    field_lower = field.lower().strip()
    patterns = FIELD_LEXICON.get(field_lower)
    if not patterns:
        patterns = [re.compile(re.escape(field_lower), re.IGNORECASE)]

    best_line = None
    best_score = -1

    for idx, line_obj in enumerate(logical):
        raw = line_obj.get("text") or ""
        if not raw.strip():
            continue
        norm = _normalize_text(raw)
        if not norm:
            continue

        matched = False
        for pat in patterns:
            if pat.search(raw) or pat.search(norm):
                matched = True
                break
        if not matched:
            continue

        score = 0
        # +1 if close to section header (first 10 lines)
        if idx < 10:
            score += 1
        # +2 if contains numeric value
        if field_lower in ("blood pressure", "bp"):
            if re.search(r"\d{2,3}/\d{2,3}", raw):  # 126/61
                score += 2
        elif field_lower in ("pulse", "heart rate"):
            if re.search(r"\b\d{2,3}\b", raw):
                score += 2
        elif field_lower in ("respiratory rate", "resp", "rr"):
            if re.search(r"\b\d{2,3}\b", raw):
                score += 2
        elif field_lower in ("spo2", "sp02", "o2"):
            if re.search(r"\b\d{2,3}\s*%?", raw):
                score += 2
        elif field_lower in ("mean arterial pressure", "map"):
            if re.search(r"\b\d{2,3}\b", raw):
                score += 2
        elif field_lower in ("level of consciousness", "loc"):
            if re.search(r"\b(awake|alert|conscious|oriented)\b", raw, re.IGNORECASE):
                score += 2
        elif field_lower in ("gcs", "glasgow"):
            if re.search(r"\b\d{1,2}\b", raw):
                score += 2
        else:
            if re.search(r"\b\d{2,3}\b", raw):
                score += 2

        if score > best_score:
            best_score = score
            best_line = line_obj

    return best_line


def build_flowsheet_sections(lines: list[dict], lines_by_page: dict[int, list[dict]]) -> list[dict]:
    """
    Build flowsheet sections grouped by (activity_date, time).
    Handles Activity Date and Time on separate lines (table layout).
    "(continued)" blocks merge into the SAME section for that (date,time).
    """
    sections: list[dict] = []
    sections_by_key: dict[tuple[str, str], dict] = {}
    current_key: tuple[str, str] | None = None
    pending_activity_date: str | None = None

    for page_num in sorted(lines_by_page.keys()):
        page_lines = lines_by_page[page_num]
        for ln in page_lines:
            text = ln.get("text", "") or ""
            if _is_skip_line(text):
                continue

            m_date = ACTIVITY_DATE_RE.search(text)
            m_time = TIME_RE.search(text)
            is_continued = bool(CONTINUED_RE.search(text))

            if m_date:
                pending_activity_date = _norm_date(m_date.group(1) or m_date.group(2) or "")

            activity_date = pending_activity_date or (current_key[0] if current_key else "")
            time_str = ""
            if m_time:
                h, m = m_time.group(1), m_time.group(2)
                if m is not None:
                    time_str = _norm_time(h + m) or (h.zfill(2) + m)
                elif len(h) in (3, 4):
                    time_str = _norm_time(h)
                else:
                    time_str = _norm_time(h + "00")

            # Create/merge section only when we have Time (date from pending or current)
            if m_time and activity_date and time_str:
                key = (activity_date, time_str)
                if key in sections_by_key and (is_continued or not m_date):
                    current_key = key
                else:
                    current_key = key
                    current_section = {
                        "page": page_num,
                        "activity_date": activity_date,
                        "time": time_str,
                        "lines": [],
                    }
                    sections_by_key[key] = current_section
                    sections.append(current_section)
                pending_activity_date = None

            if m_date or m_time:
                continue

            # Add vitals to current section (skip header lines)
            if current_key and current_key in sections_by_key:
                current_section = sections_by_key[current_key]
                is_header = bool(ACTIVITY_DATE_RE.search(text))
                if not is_header and text.strip():
                    current_section["lines"].append({
                        "line_id": ln.get("line_id"),
                        "page": page_num,
                        "text": text,
                        "bbox": ln.get("bbox"),
                        "y0": ln.get("bbox", [0, 0, 0, 0])[1] if ln.get("bbox") else 0,
                    })

    return sections


def _page_is_flowsheet(page_lines: list[dict]) -> bool:
    concat = " ".join(ln.get("text", "") or "" for ln in page_lines)
    return bool(FLOWSHEET_MARKER_RE.search(concat))


def build_flowsheet_sections_from_lines(lines: list[dict]) -> list[dict]:
    lines_by_page: dict[int, list[dict]] = defaultdict(list)
    for ln in lines:
        lines_by_page[ln["page"]].append(ln)
    flowsheet_pages = {p for p, pl in lines_by_page.items() if _page_is_flowsheet(pl)}
    if not flowsheet_pages:
        return []
    filtered_by_page = {p: lines_by_page[p] for p in flowsheet_pages}
    return build_flowsheet_sections(lines, filtered_by_page)


def is_flowsheet_question(question: str) -> bool:
    """Trigger ONLY if question has time AND flowsheet field keyword."""
    q = (question or "").lower()
    has_time = bool(TIME_PATTERN_RE.search(question or ""))
    has_vital = any(kw in q for kw in VITALS_KEYWORDS)
    return has_time and has_vital


def _most_common_activity_date(sections: list[dict]) -> str | None:
    dates = [s.get("activity_date") for s in sections if s.get("activity_date")]
    if not dates:
        return None
    c = Counter(_norm_date(d) for d in dates)
    return c.most_common(1)[0][0]


def extract_flowsheet_params(
    question: str,
    flowsheet_sections: list[dict] | None = None,
) -> tuple[str | None, str | None, str | None]:
    """
    Parse date, time, field from question.
    If date missing, use most common Activity Date from flowsheet sections.
    """
    q = (question or "").lower()
    date_str = None
    m = re.search(r"\b(\d{1,2})/(\d{1,2})/(\d{2,4})\b", question or "")
    if m:
        parts = m.group(0).split("/")
        mo, d = parts[0].zfill(2), parts[1].zfill(2)
        yr = parts[2][-2:] if len(parts[2]) >= 2 else parts[2]
        date_str = f"{mo}/{d}/{yr}"
    month_map = {"january": "01", "jan": "01", "february": "02", "feb": "02", "march": "03", "mar": "03",
                 "april": "04", "apr": "04", "may": "05", "june": "06", "jun": "06", "july": "07", "jul": "07",
                 "august": "08", "aug": "08", "september": "09", "sep": "09", "october": "10", "oct": "10",
                 "november": "11", "nov": "11", "december": "12", "dec": "12"}
    for name, num in month_map.items():
        if name in q:
            dm = re.search(rf"{name}\s+(\d{{1,2}})", q)
            if dm:
                date_str = f"{num}/{dm.group(1).zfill(2)}/24"
                break

    if not date_str and flowsheet_sections:
        date_str = _most_common_activity_date(flowsheet_sections)

    time_str = None
    m = re.search(r"(?:^|[\s,])(\d{1,2}):(\d{2})\b", question or "")
    if m:
        time_str = _norm_time(m.group(1) + m.group(2))
    if not time_str:
        m = re.search(r"\b(\d{3,4})\b", question or "")
        if m:
            t = m.group(1)
            val = int(t)
            if 100 <= val < 2400 and val % 100 < 60:
                time_str = t.zfill(4)

    field = None
    field_map = [
        ("blood pressure", ["blood pressure", "bp", "blood"]),
        ("pulse", ["pulse", "heart rate"]),
        ("respiratory rate", ["respiratory rate", "rr", "resp"]),
        ("spo2", ["spo2", "sp02", "spo2", "oxygen", "o2"]),
        ("mean arterial pressure", ["mean arterial pressure", "map"]),
        ("level of consciousness", ["level of consciousness", "loc", "consciousness"]),
        ("gcs", ["gcs", "glasgow"]),
        ("pupil", ["pupil"]),
        ("neuro", ["neuro"]),
    ]
    for canonical, aliases in field_map:
        if any(a in q for a in aliases):
            field = canonical
            break

    return (date_str, time_str, field) if (date_str or time_str) and field else (None, None, None)


def get_flowsheet_answer(
    question: str,
    flowsheet_sections: list[dict],
) -> tuple[str | None, list[dict]]:
    """
    Find section by (date,time), then find_value_line for field.
    Returns (answer_text, evidence_lines). Uses stored bbox only for highlights.
    """
    if not flowsheet_sections or not is_flowsheet_question(question):
        return None, []
    date_str, time_str, field = extract_flowsheet_params(question, flowsheet_sections)
    if not field:
        return None, []

    best_section = None
    for sec in flowsheet_sections:
        sec_date = _norm_date(sec.get("activity_date", ""))
        sec_time = _norm_time(sec.get("time", ""))
        date_ok = not date_str or not sec_date or sec_date == _norm_date(date_str)
        time_ok = not time_str or not sec_time or sec_time == _norm_time(time_str)
        if date_ok and time_ok:
            best_section = sec
            break

    if not best_section or not best_section.get("lines"):
        logger.debug("flowsheet: no section found for date=%s time=%s", date_str, time_str)
        return None, []

    line_obj = find_value_line(best_section["lines"], field)
    if not line_obj:
        logger.debug("flowsheet: no line matched for field=%s in section date=%s time=%s", field, best_section.get("activity_date"), best_section.get("time"))
        return None, []

    logger.info(
        "flowsheet: section found date=%s time=%s | line matched field=%s text=%s",
        best_section.get("activity_date"), best_section.get("time"), field, (line_obj.get("text") or "")[:60]
    )
    answer = (line_obj.get("text") or "").strip()
    evidence = [{
        "line_id": line_obj.get("line_id"),
        "page": line_obj.get("page"),
        "text": line_obj.get("text"),
        "bbox": line_obj.get("bbox"),
    }]
    return answer, evidence
