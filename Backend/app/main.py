# main.py
"""PDF Q&A with Line-ID grounded highlights."""

import re
from collections import defaultdict

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse, Response
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .schemas import UploadResponse, AskRequest, AskResponse, EvidenceItem, HighlightItem, ExportHighlightedRequest
from .storage import ensure_dirs, sha256_bytes, save_pdf, pdf_path, artifact_path, save_artifact, load_artifact
from .lines import build_lines_from_words
from .retrieve import top_k_lines_with_context, extract_date_from_question
from .llm import ask_llm
from .flowsheet import (
    build_flowsheet_sections_from_lines,
    is_flowsheet_question,
    get_flowsheet_answer,
)
import os

SIGNED_INTENT_RE = re.compile(r"\b(signed|signature|who signed|signers?|discharge)\b", re.IGNORECASE)
SIGNER_RE = re.compile(
    r"(?:Signed by|Electronically signed by)\s+([A-Za-z][A-Za-z.,\s\-]+?)(?:\s+on\s|\s*$)",
    re.IGNORECASE,
)
ORDERING_DOCTOR_RE = re.compile(r"Ordering Doctor:\s*([A-Za-z][A-Za-z.,\s\-]+?)(?:\s{2,}|\d|$)", re.IGNORECASE)

ORDERING_DOCTOR_DATE_PROXIMITY = 10


def _line_contains_question_date(ln: dict, question_date: str) -> bool:
    """Check if line text contains the question date (04/06/24, 4/6/24, April 6, apr 6)."""
    if not question_date:
        return False
    t = ln.get("text", "") or ""
    if question_date in t:
        return True
    parts = question_date.split("/")
    if len(parts) == 3:
        if f"{int(parts[0])}/{int(parts[1])}/{parts[2]}" in t:
            return True
        month_abbrev = {"01": "jan", "02": "feb", "03": "mar", "04": "apr", "05": "may", "06": "jun",
                        "07": "jul", "08": "aug", "09": "sep", "10": "oct", "11": "nov", "12": "dec"}
        month_full = {"01": "january", "02": "february", "03": "march", "04": "april", "05": "may", "06": "june",
                      "07": "july", "08": "august", "09": "september", "10": "october", "11": "november", "12": "december"}
        if parts[0] in month_abbrev:
            d = str(int(parts[1]))
            tl = t.lower()
            if f"{month_abbrev[parts[0]]} {d}" in tl or f"{month_abbrev[parts[0]]} {parts[1]}" in tl:
                return True
            if parts[0] in month_full and f"{month_full[parts[0]]} {d}" in tl:
                return True
    return False


def _find_ordering_doctor_fallback(
    candidates: list[dict],
    all_lines: list[dict],
    question_date: str | None,
) -> tuple[list[dict], list[str]]:
    """
    When Signed lines are garbled, try clean 'Ordering Doctor: Name' lines.
    Only include an Ordering Doctor if within ±N lines of a line containing the question date.
    """
    if not question_date:
        return [], []
    signers = []
    evidence_lines = []
    date_hit_pages = {ln["page"] for ln in candidates}
    lines_by_page: dict[int, list[dict]] = defaultdict(list)
    for ln in all_lines:
        lines_by_page[ln["page"]].append(ln)
    for ln in all_lines:
        if ln["page"] not in date_hit_pages:
            continue
        t = ln.get("text", "")
        m = ORDERING_DOCTOR_RE.search(t)
        if not m:
            continue
        page_lines = lines_by_page[ln["page"]]
        idx = next((i for i, l in enumerate(page_lines) if l.get("line_id") == ln.get("line_id")), -1)
        if idx < 0:
            continue
        start = max(0, idx - ORDERING_DOCTOR_DATE_PROXIMITY)
        end = min(len(page_lines), idx + ORDERING_DOCTOR_DATE_PROXIMITY + 1)
        has_date_nearby = any(_line_contains_question_date(page_lines[i], question_date) for i in range(start, end))
        if not has_date_nearby:
            continue
        name = m.group(1).strip().rstrip(".,")
        if name and len(name) > 2 and name not in signers and not _is_garbled_name(name):
            signers.append(name)
            evidence_lines.append(ln)
    return evidence_lines, signers


def _is_garbled_name(name: str) -> bool:
    """Detect encoding-corrupted names (font/encoding artifacts in PDF extraction)."""
    if not name or len(name) < 3:
        return True
    n = name.strip()
    vowels = set("aeiouAEIOU")
    consonant_streak = 0
    for c in n:
        if c.isalpha():
            if c in vowels:
                consonant_streak = 0
            else:
                consonant_streak += 1
                if consonant_streak >= 4:
                    return True  # encoding artifacts
        else:
            consonant_streak = 0  # reset on space, comma, etc.
    # Odd alternating case (PwSnSlO)
    if len(n) >= 5 and n == n.swapcase():
        return True
    # Single word, no comma/space, very caps-heavy
    if "," not in n and " " not in n and len(n) >= 5:
        if sum(1 for c in n if c.isupper()) > len([c for c in n if c.isalpha()]) // 2:
            return True
    # Known garbled pattern: 3+ caps then lowercase then cap
    if re.search(r"[A-Z]{3,}[a-z][A-Z]|[a-z][A-Z]{3,}[a-z]", n):
        return True
    return False

app = FastAPI(title="PDF Q&A with Highlights")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def _startup():
    ensure_dirs()


@app.post("/documents", response_model=UploadResponse)
async def upload_document(file: UploadFile = File(...), force: bool = False):
    """Upload a PDF. Use ?force=true to re-extract and rebuild artifacts."""
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Only PDF files are supported.")
    b = await file.read()
    if not b:
        raise HTTPException(400, "Empty file.")
    doc_id = sha256_bytes(b)
    pdf_fp = pdf_path(doc_id)
    art_path = artifact_path(doc_id)
    if not os.path.exists(pdf_fp):
        save_pdf(doc_id, b)
    if not os.path.exists(art_path) or force:
        line_data = build_lines_from_words(pdf_fp)
        flowsheet_sections = build_flowsheet_sections_from_lines(line_data["lines"])
        save_artifact(doc_id, {
            "doc_id": doc_id,
            "filename": file.filename,
            "page_count": line_data["page_count"],
            "pages": line_data["pages"],
            "lines": line_data["lines"],
            "flowsheet_sections": flowsheet_sections,
        })
    art = load_artifact(doc_id)
    return UploadResponse(doc_id=doc_id, filename=art["filename"], page_count=art["page_count"])


@app.get("/documents/{doc_id}/file")
def get_pdf(doc_id: str):
    fp = pdf_path(doc_id)
    if not os.path.exists(fp):
        raise HTTPException(404, "Document not found.")
    return FileResponse(fp, media_type="application/pdf", filename=f"{doc_id}.pdf")


def _add_highlights_to_pdf(pdf_path_str: str, highlights: list[dict]) -> bytes:
    """Add highlight annotations to PDF and return bytes."""
    import fitz
    doc = fitz.open(pdf_path_str)
    try:
        by_page: dict[int, list] = {}
        for h in highlights:
            page = int(h.get("page", 0))
            rects = h.get("rects", [])
            if page and rects:
                by_page.setdefault(page, []).extend(rects)
        for page_num, rects in by_page.items():
            if page_num < 1 or page_num > len(doc):
                continue
            page = doc[page_num - 1]
            for r in rects:
                if len(r) >= 4:
                    x0, y0, x1, y1 = float(r[0]), float(r[1]), float(r[2]), float(r[3])
                    rect = fitz.Rect(x0, y0, x1, y1)
                    try:
                        annot = page.add_highlight_annot([rect])
                        annot.set_colors(stroke=(1, 0, 0))  # red
                        annot.update()
                    except Exception:
                        pass
        return doc.write()
    finally:
        doc.close()


@app.post("/documents/{doc_id}/export-highlighted")
def export_highlighted(doc_id: str, req: ExportHighlightedRequest):
    """Return PDF with highlight annotations burned in. Use when highlights exist."""
    fp = pdf_path(doc_id)
    if not os.path.exists(fp):
        raise HTTPException(404, "Document not found.")
    art = load_artifact(doc_id)
    filename = (art.get("filename") or f"{doc_id}.pdf").replace(".pdf", "_highlighted.pdf")
    if not req.highlights:
        return FileResponse(fp, media_type="application/pdf", filename=filename)
    highlights_data = [{"page": h.page, "rects": h.rects} for h in req.highlights]
    pdf_bytes = _add_highlights_to_pdf(fp, highlights_data)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def _build_lines_by_id(lines: list[dict]) -> dict[str, dict]:
    return {ln["line_id"]: ln for ln in lines}


def _extract_signers_deterministic(candidates: list[dict], question_date: str | None) -> tuple[list[dict], list[str]]:
    """
    For "who signed on date X" questions: extract signers via regex from date-filtered Signed lines.
    Filters out garbled names (encoding corruption). Returns (evidence_lines, signer_names).
    """
    signers = []
    evidence_lines = []
    for ln in candidates:
        t = ln.get("text", "")
        if "signed" not in t.lower():
            continue
        if question_date and question_date not in t:
            continue
        m = SIGNER_RE.search(t)
        if m:
            name = m.group(1).strip().rstrip(".,")
            if name and len(name) > 2 and name not in signers and not _is_garbled_name(name):
                signers.append(name)
                evidence_lines.append(ln)
    return evidence_lines, signers


@app.post("/documents/{doc_id}/ask", response_model=AskResponse)
def ask(doc_id: str, req: AskRequest):
    if not req.question.strip():
        raise HTTPException(400, "Question cannot be empty.")
    fp = pdf_path(doc_id)
    if not os.path.exists(fp):
        raise HTTPException(404, "Document not found.")
    art = load_artifact(doc_id)
    lines = art.get("lines", [])
    if not lines and art.get("chunks"):
        # Old artifact format - auto-rebuild with line-based extraction
        line_data = build_lines_from_words(fp)
        flowsheet_sections = build_flowsheet_sections_from_lines(line_data["lines"])
        art = {
            "doc_id": doc_id,
            "filename": art.get("filename", ""),
            "page_count": line_data["page_count"],
            "pages": line_data["pages"],
            "lines": line_data["lines"],
            "flowsheet_sections": flowsheet_sections,
        }
        save_artifact(doc_id, art)
        lines = line_data["lines"]
    if not lines:
        return AskResponse(
            answer="Not found in document",
            evidence=[],
            highlights=[],
            page_dims={str(p["page"]): {"width": p["width"], "height": p["height"]} for p in art.get("pages", [])},
        )
    # Flowsheet path: time + vitals question → direct section lookup (skip RAG)
    flowsheet_sections = art.get("flowsheet_sections")
    if not flowsheet_sections and lines:
        flowsheet_sections = build_flowsheet_sections_from_lines(lines)
    if flowsheet_sections and is_flowsheet_question(req.question):
        answer_text, ev_lines = get_flowsheet_answer(req.question, flowsheet_sections)
        if answer_text and ev_lines:
            evidence_items = [EvidenceItem(page=ln["page"], line_id=ln.get("line_id", ""), text=ln.get("text", "")) for ln in ev_lines]
            highlights_by_page: dict[int, list] = {}
            for ln in ev_lines:
                bbox = ln.get("bbox")
                if bbox and len(bbox) >= 4:
                    highlights_by_page.setdefault(ln["page"], []).append(bbox)
            highlight_items = [HighlightItem(page=p, rects=rects) for p, rects in sorted(highlights_by_page.items())]
            page_dims = {str(p["page"]): {"width": p["width"], "height": p["height"]} for p in art.get("pages", [])}
            return AskResponse(answer=answer_text, evidence=evidence_items, highlights=highlight_items, page_dims=page_dims)
    # Line-based retrieval (date-filtered when question mentions date)
    candidates = top_k_lines_with_context(req.question, lines, k=20, context_lines=2)
    if not candidates:
        return AskResponse(
            answer="Not found in document",
            evidence=[],
            highlights=[],
            page_dims={str(p["page"]): {"width": p["width"], "height": p["height"]} for p in art.get("pages", [])},
        )
    question_date = extract_date_from_question(req.question)
    # Deterministic path: "who signed on date X" -> extract signers via regex, bypass LLM
    # Fallback to "Ordering Doctor:" when Signed lines are garbled (encoding corruption)
    if SIGNED_INTENT_RE.search(req.question) and question_date:
        ev_lines, signers = _extract_signers_deterministic(candidates, question_date)
        if not signers:
            ev_lines, signers = _find_ordering_doctor_fallback(candidates, lines, question_date)
        if signers:
            lines_by_id = _build_lines_by_id(lines)
            evidence_items = [EvidenceItem(page=ln["page"], line_id=ln["line_id"], text=ln["text"]) for ln in ev_lines]
            highlights_by_page: dict[int, list] = {}
            for ln in ev_lines:
                bbox = ln.get("bbox")
                if bbox and len(bbox) >= 4:
                    highlights_by_page.setdefault(ln["page"], []).append(bbox)
            answer = " and ".join(signers) if len(signers) > 1 else signers[0]
            highlight_items = [HighlightItem(page=p, rects=rects) for p, rects in sorted(highlights_by_page.items())]
            page_dims = {str(p["page"]): {"width": p["width"], "height": p["height"]} for p in art.get("pages", [])}
            return AskResponse(answer=answer, evidence=evidence_items, highlights=highlight_items, page_dims=page_dims)
    # LLM path
    llm_out = ask_llm(req.question, candidates, question_date=question_date)
    evidence_line_ids = llm_out.get("evidence_line_ids", []) or []
    answer = (llm_out.get("answer") or "Not found in document").strip()
    lines_by_id = _build_lines_by_id(lines)
    # Deterministic highlights: lookup bbox from lines_by_id
    evidence_items = []
    highlights_by_page: dict[int, list] = {}
    for lid in evidence_line_ids[:5]:
        ln = lines_by_id.get(lid)
        if not ln:
            continue
        page = ln["page"]
        evidence_items.append(EvidenceItem(page=page, line_id=lid, text=ln["text"]))
        bbox = ln.get("bbox")
        if bbox and len(bbox) >= 4:
            highlights_by_page.setdefault(page, []).append(bbox)
    highlight_items = [
        HighlightItem(page=page, rects=rects)
        for page, rects in sorted(highlights_by_page.items())
    ]
    page_dims = {str(p["page"]): {"width": p["width"], "height": p["height"]} for p in art.get("pages", [])}
    return AskResponse(
        answer=answer,
        evidence=evidence_items,
        highlights=highlight_items,
        page_dims=page_dims,
    )
