# schemas.py
from pydantic import BaseModel, Field
from typing import List, Optional, Tuple

Rect = Tuple[float, float, float, float]

class UploadResponse(BaseModel):
    doc_id: str
    filename: str
    page_count: int

class AskRequest(BaseModel):
    question: str = Field(min_length=1)

class EvidenceItem(BaseModel):
    page: int
    line_id: str
    text: str

class HighlightItem(BaseModel):
    page: int
    rects: List[Rect]

class AskResponse(BaseModel):
    answer: str
    evidence: List[EvidenceItem]
    highlights: List[HighlightItem]
    page_dims: Optional[dict[str, dict[str, float]]] = None  # {"1": {"width": 612, "height": 792}, ...}


class ExportHighlightedRequest(BaseModel):
    highlights: List[HighlightItem] = []
