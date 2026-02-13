# lines.py
"""Line-ID grounded extraction: pdfplumber (better encoding) or PyMuPDF fallback."""

import re
from collections import defaultdict

try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False
try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False


def _norm_text(s: str) -> str:
    s = (s or "").replace("\u00a0", " ")
    return re.sub(r"\s+", " ", s).strip()


def _build_from_pdfplumber(pdf_path: str) -> dict | None:
    """pdfplumber often handles encoding better for clinical PDFs."""
    if not PDFPLUMBER_AVAILABLE:
        return None
    try:
        with pdfplumber.open(pdf_path) as doc:
            lines_list: list[dict] = []
            lines_by_id: dict[str, dict] = {}
            lines_by_page: dict[int, list] = defaultdict(list)
            pages: list[dict] = []
            for i, page in enumerate(doc.pages):
                page_num = i + 1
                w, h = float(page.width or 612), float(page.height or 792)
                pages.append({"page": page_num, "width": w, "height": h})
                words_raw = page.extract_words(x_tolerance=3, y_tolerance=3) or []
                # Group words by similar y (same line)
                y_groups: dict[float, list] = defaultdict(list)
                for w in words_raw:
                    txt = (w.get("text") or "").strip()
                    if not txt:
                        continue
                    x0, top, x1, bottom = (
                        float(w.get("x0", 0)), float(w.get("top", 0)),
                        float(w.get("x1", 0)), float(w.get("bottom", 0)),
                    )
                    y_key = round(top, 1)
                    y_groups[y_key].append({"text": txt, "x0": x0, "y0": top, "x1": x1, "y1": bottom})
                for line_idx, (y_key, line_words) in enumerate(sorted(y_groups.items())):
                    if not line_words:
                        continue
                    line_id = f"p{page_num}_b0_l{line_idx}"
                    text = _norm_text(" ".join(w["text"] for w in line_words))
                    if not text:
                        continue
                    x0 = min(w["x0"] for w in line_words)
                    y0 = min(w["y0"] for w in line_words)
                    x1 = max(w["x1"] for w in line_words)
                    y1 = max(w["y1"] for w in line_words)
                    bbox = [x0, y0, x1, y1]
                    line = {"line_id": line_id, "page": page_num, "text": text, "bbox": bbox, "words": line_words}
                    lines_list.append(line)
                    lines_by_id[line_id] = line
                    lines_by_page[page_num].append(line)
            if lines_list:
                return {
                    "lines": lines_list,
                    "lines_by_id": lines_by_id,
                    "lines_by_page": dict(lines_by_page),
                    "pages": pages,
                    "page_count": len(pages),
                }
    except Exception:
        pass
    return None


def build_lines_from_words(pdf_path: str) -> dict:
    """
    Extract structured lines from PDF.
    Uses pdfplumber first (better encoding for clinical PDFs), PyMuPDF fallback.
    Returns: {lines, lines_by_id, lines_by_page, pages, page_count}
    """
    result = _build_from_pdfplumber(pdf_path)
    if result:
        return result
    if not PYMUPDF_AVAILABLE:
        raise RuntimeError("PyMuPDF is required for line extraction")
    doc = fitz.open(pdf_path)
    lines: list[dict] = []
    lines_by_id: dict[str, dict] = {}
    lines_by_page: dict[int, list[dict]] = defaultdict(list)
    pages: list[dict] = []
    try:
        for page_idx, page in enumerate(doc):
            page_num = page_idx + 1
            rect = page.rect
            pages.append({
                "page": page_num,
                "width": float(rect.width),
                "height": float(rect.height),
            })
            words_raw = page.get_text("words", sort=True) or []
            # PyMuPDF word: (x0, y0, x1, y1, "text", block_no, line_no)
            words = []
            for w in words_raw:
                if len(w) >= 7 and (w[4] or "").strip():
                    words.append({
                        "text": str(w[4]).strip(),
                        "x0": float(w[0]), "y0": float(w[1]),
                        "x1": float(w[2]), "y1": float(w[3]),
                        "block": int(w[5]), "line": int(w[6]),
                    })
            # Group by (block_no, line_no)
            groups: dict[tuple[int, int], list] = defaultdict(list)
            for w in words:
                groups[(w["block"], w["line"])].append(w)
            # Build lines
            for (block_no, line_no), line_words in sorted(groups.items()):
                if not line_words:
                    continue
                line_id = f"p{page_num}_b{block_no}_l{line_no}"
                text = " ".join(w["text"] for w in line_words)
                text = _norm_text(text)
                if not text:
                    continue
                x0 = min(w["x0"] for w in line_words)
                y0 = min(w["y0"] for w in line_words)
                x1 = max(w["x1"] for w in line_words)
                y1 = max(w["y1"] for w in line_words)
                bbox = [x0, y0, x1, y1]
                line = {
                    "line_id": line_id,
                    "page": page_num,
                    "text": text,
                    "bbox": bbox,
                    "words": line_words,
                }
                lines.append(line)
                lines_by_id[line_id] = line
                lines_by_page[page_num].append(line)
        return {
            "lines": lines,
            "lines_by_id": lines_by_id,
            "lines_by_page": dict(lines_by_page),
            "pages": pages,
            "page_count": len(pages),
        }
    finally:
        doc.close()
