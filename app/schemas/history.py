from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.resume import ResumeAnalysisResponse


class ResumeHistoryItem(BaseModel):
    id: int
    filename: str
    analysis_count: int = Field(ge=0)
    created_at: datetime


class ResumeHistoryPage(BaseModel):
    items: list[ResumeHistoryItem]
    total: int = Field(ge=0)
    page: int = Field(ge=1)
    page_size: int = Field(ge=1)
    pages: int = Field(ge=0)


class AnalysisHistoryItem(BaseModel):
    id: int
    resume_id: int
    resume_filename: str
    score: int = Field(ge=0, le=100)
    job_title: str
    job_description_preview: str
    created_at: datetime


class AnalysisHistoryPage(BaseModel):
    items: list[AnalysisHistoryItem]
    total: int = Field(ge=0)
    page: int = Field(ge=1)
    page_size: int = Field(ge=1)
    pages: int = Field(ge=0)


class AnalysisHistoryDetail(AnalysisHistoryItem):
    job_description: str | None
    result: ResumeAnalysisResponse


class ChatHistoryItem(BaseModel):
    id: int
    question: str
    answer: str
    sources: list[str] = Field(default_factory=list)
    created_at: datetime


class ChatHistoryPage(BaseModel):
    items: list[ChatHistoryItem]
    total: int = Field(ge=0)
    page: int = Field(ge=1)
    page_size: int = Field(ge=1)
    pages: int = Field(ge=0)
