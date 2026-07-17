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


class KnowledgeChatRequest(BaseModel):
    question: KnowledgeQuestion


class KnowledgeChatResponse(BaseModel):
    answer: str
    sources: list[str]
