# extract.py
"""Extract text from PDFs. Uses pdfplumber (primary) with PyMuPDF fallback for reliability."""

import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Try pdfplumber first (better text fidelity for many PDFs)
try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False

try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False


def _extract_with_pdfplumber(pdf_file_path: str) -> Optional[dict]:
    """Extract using pdfplumber - often better for font/encoding issues."""
    if not PDFPLUMBER_AVAILABLE:
        return None
    try:
        with pdfplumber.open(pdf_file_path) as doc:
            pages = []
            for i, page in enumerate(doc.pages):
                # Use layout=True for better structure; x_tolerance/y_tolerance for word grouping
                text = page.extract_text(layout=True, x_tolerance=2, y_tolerance=2)
                if not text:
                    text = page.extract_text(layout=False) or ""
                text = (text or "").strip()

                # Extract words for potential highlight use (x0, top, x1, bottom)
                words_raw = page.extract_words(x_tolerance=2, y_tolerance=2) or []
                words = [
                    {
                        "t": w.get("text", ""),
                        "x0": float(w.get("x0", 0)),
                        "y0": float(w.get("top", 0)),
                        "x1": float(w.get("x1", 0)),
                        "y1": float(w.get("bottom", 0)),
                    }
                    for w in words_raw if w.get("text")
                ]

                w, h = page.width or 612, page.height or 792
                pages.append({
                    "page": i + 1,
                    "text": text,
                    "words": words,
                    "width": float(w),
                    "height": float(h),
                })

            return {"page_count": len(pages), "pages": pages}
    except Exception as e:
        logger.warning("pdfplumber extraction failed: %s", e)
        return None


def _extract_with_pymupdf(pdf_file_path: str) -> dict:
    """Extract using PyMuPDF (fallback)."""
    if not PYMUPDF_AVAILABLE:
        raise RuntimeError("Neither pdfplumber nor PyMuPDF available for extraction")
    doc = fitz.open(pdf_file_path)
    pages = []
    try:
        for i, page in enumerate(doc):
            blocks = page.get_text("blocks", sort=True) or []
            text_parts = [b[4].strip() for b in blocks if len(b) >= 5 and b[4]]
            text = "\n".join(text_parts) if text_parts else (page.get_text("text", sort=True) or "")

            words_raw = page.get_text("words", sort=True) or []
            words = [
                {"t": w[4], "x0": float(w[0]), "y0": float(w[1]), "x1": float(w[2]), "y1": float(w[3]),
                 "block": int(w[5]), "line": int(w[6])}
                for w in words_raw
            ]
            pages.append({
                "page": i + 1,
                "text": text,
                "words": words,
                "width": float(page.rect.width),
                "height": float(page.rect.height),
            })
        return {"page_count": doc.page_count, "pages": pages}
    finally:
        doc.close()


def extract_pdf(pdf_file_path: str) -> dict:
    """
    Extract text and word positions from a PDF.
    Uses pdfplumber first (better encoding handling), falls back to PyMuPDF.
    """
    result = _extract_with_pdfplumber(pdf_file_path)
    if result is not None and result.get("pages"):
        # Validate we got non-empty text from at least one page
        has_text = any(p.get("text", "").strip() for p in result["pages"])
        if has_text:
            return result
    return _extract_with_pymupdf(pdf_file_path)
