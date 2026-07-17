import httpx
import pytest

from app.core.exceptions import LLMServiceError
from app.main import app
from app.schemas.resume import ResumeAnalysisResponse
from app.services.resume_analyzer import get_resume_analyzer_service


class SuccessfulResumeAnalyzer:
    async def analyze(
        self,
        resume_text: str,
        job_description: str,
    ) -> ResumeAnalysisResponse:
        assert "Python" in resume_text
        assert "Kubernetes" in job_description
        return ResumeAnalysisResponse(
            score=85,
            matching_skills=["Python", "FastAPI"],
            missing_skills=["Kubernetes"],
            resume_advices=["补充项目的量化成果"],
            interview_questions=["如何设计高可用 API？"],
        )


class FailingResumeAnalyzer:
    async def analyze(self, resume_text: str, job_description: str) -> ResumeAnalysisResponse:
        raise LLMServiceError


async def post_analysis(payload: dict[str, str]) -> httpx.Response:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.post("/api/v1/resume/analyze", json=payload)


@pytest.mark.asyncio
async def test_resume_analysis_returns_structured_result() -> None:
    app.dependency_overrides[get_resume_analyzer_service] = SuccessfulResumeAnalyzer
    try:
        response = await post_analysis(
            {
                "resume_text": "三年 Python 和 FastAPI 开发经验。",
                "job_description": "要求 Python、FastAPI 和 Kubernetes。",
            }
        )
    finally:
        app.dependency_overrides.pop(get_resume_analyzer_service, None)

    assert response.status_code == 200
    assert response.json() == {
        "score": 85,
        "matching_skills": ["Python", "FastAPI"],
        "missing_skills": ["Kubernetes"],
        "resume_advices": ["补充项目的量化成果"],
        "interview_questions": ["如何设计高可用 API？"],
    }


@pytest.mark.asyncio
async def test_resume_analysis_rejects_blank_resume() -> None:
    app.dependency_overrides[get_resume_analyzer_service] = SuccessfulResumeAnalyzer
    try:
        response = await post_analysis(
            {
                "resume_text": "   ",
                "job_description": "要求 Python 开发经验。",
            }
        )
    finally:
        app.dependency_overrides.pop(get_resume_analyzer_service, None)

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_resume_analysis_handles_model_failure() -> None:
    app.dependency_overrides[get_resume_analyzer_service] = FailingResumeAnalyzer
    try:
        response = await post_analysis(
            {
                "resume_text": "Python 开发经验。",
                "job_description": "要求 Python 开发经验。",
            }
        )
    finally:
        app.dependency_overrides.pop(get_resume_analyzer_service, None)

    assert response.status_code == 502
    assert response.json()["code"] == "llm_service_error"
