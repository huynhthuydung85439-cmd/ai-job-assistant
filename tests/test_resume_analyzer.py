import pytest
from langchain_core.language_models import FakeListChatModel

from app.core.exceptions import LLMServiceError
from app.services.resume_analyzer import ResumeAnalyzerService


@pytest.mark.asyncio
async def test_resume_analyzer_parses_structured_model_output() -> None:
    model = FakeListChatModel(
        responses=[
            """{
                "score": 85,
                "matching_skills": ["Python", "FastAPI"],
                "missing_skills": ["Kubernetes"],
                "resume_advices": ["补充 FastAPI 项目的量化成果"],
                "interview_questions": ["如何设计高并发 FastAPI 服务？"]
            }"""
        ]
    )
    service = ResumeAnalyzerService(model)

    result = await service.analyze(
        resume_text="具备 Python 和 FastAPI 项目经验。",
        job_description="招聘 Python 工程师，要求 FastAPI 和 Kubernetes。",
    )

    assert result.score == 85
    assert result.matching_skills == ["Python", "FastAPI"]
    assert result.missing_skills == ["Kubernetes"]
    assert result.resume_advices == ["补充 FastAPI 项目的量化成果"]
    assert result.interview_questions == ["如何设计高并发 FastAPI 服务？"]


@pytest.mark.asyncio
async def test_resume_analyzer_rejects_invalid_model_output() -> None:
    service = ResumeAnalyzerService(FakeListChatModel(responses=['{"score": 120}']))

    with pytest.raises(LLMServiceError):
        await service.analyze(
            resume_text="Python 开发经验。",
            job_description="招聘 Python 工程师。",
        )
