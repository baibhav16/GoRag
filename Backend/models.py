from pydantic import BaseModel
from typing import Any, List, Literal, Optional


class AskRequest(BaseModel):
    query: str
    doc_id: str


class VisualEvidence(BaseModel):
    id: str
    type: Literal["image", "table"]
    page: int
    caption: Optional[str] = None
    src: Optional[str] = None
    tableData: Optional[List[List[Any]]] = None


class AskResponse(BaseModel):
    answer: str
    citations: List[int]
    supporting_visuals: List[VisualEvidence]
    doc_id: str
