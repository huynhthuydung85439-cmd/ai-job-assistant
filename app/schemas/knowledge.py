from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field, StringConstraints

KnowledgeQuestion = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=10_000),
]


class KnowledgeUploadResponse(BaseModel):
    document_id: str
    filename: str
    pages: int = Field(gt=0)
    chunks: int = Field(gt=0)
    collection_name: str
    uploaded_at: datetime


class KnowledgeDocumentItem(KnowledgeUploadResponse):
    pass


class KnowledgeDocumentPage(BaseModel):
    items: list[KnowledgeDocumentItem]
    total: int = Field(ge=0)
    page: int = Field(ge=1)
    page_size: int = Field(ge=1)
    pages: int = Field(ge=0)


class KnowledgeChatRequest(BaseModel):
    question: KnowledgeQuestion


class KnowledgeChatResponse(BaseModel):
    answer: str
    sources: list[str]


class KnowledgeWarmupResponse(BaseModel):
    status: str
    model: str


class KnowledgeDeleteResponse(BaseModel):
    document_id: str
    deleted: bool
