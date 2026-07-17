from io import BytesIO

import httpx
import pytest
from reportlab.pdfgen import canvas

from app.main import app
from app.schemas.resume import ResumeAnalysisResponse
from app.services.resume_analyzer import get_resume_analyzer_service


def create_resume_pdf(text: str = "Python FastAPI MySQL experience") -> bytes:
    output = BytesIO()
    document = canvas.Canvas(output)
    document.drawString(72, 750, text)
    document.showPage()
    document.save()
    return output.getvalue()


class PipelineResumeAnalyzer:
    async def analyze(
        self,
        resume_text: str,
        job_description: str,
    ) -> ResumeAnalysisResponse:
        assert "Python FastAPI" in resume_text
        assert "Kubernetes" in job_description
        return ResumeAnalysisResponse(
            score=80,
            matching_skills=["Python", "FastAPI"],
            missing_skills=["Kubernetes"],
            resume_advices=["Add measurable project outcomes"],
            interview_questions=["How do you scale a FastAPI service?"],
        )


@pytest.mark.asyncio
async def test_resume_upload_extracts_pdf_text() -> None:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/resume/upload",
            files={"file": ("resume.pdf", create_resume_pdf(), "application/pdf")},
        )

    assert response.status_code == 200
    assert response.json()["filename"] == "resume.pdf"
    assert response.json()["pages"] == 1
    assert "Python FastAPI MySQL experience" in response.json()["text"]


@pytest.mark.asyncio
async def test_uploaded_text_can_be_analyzed_without_contract_changes() -> None:
    app.dependency_overrides[get_resume_analyzer_service] = PipelineResumeAnalyzer
    try:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            upload_response = await client.post(
                "/api/v1/resume/upload",
                files={"file": ("resume.pdf", create_resume_pdf(), "application/pdf")},
            )
            analysis_response = await client.post(
                "/api/v1/resume/analyze",
                json={
                    "resume_text": upload_response.json()["text"],
                    "job_description": "Python FastAPI role requiring Kubernetes",
                },
            )
    finally:
        app.dependency_overrides.pop(get_resume_analyzer_service, None)

    assert upload_response.status_code == 200
    assert analysis_response.status_code == 200
    assert analysis_response.json()["score"] == 80


@pytest.mark.asyncio
async def test_resume_upload_rejects_non_pdf_file() -> None:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/resume/upload",
            files={"file": ("resume.txt", b"plain text", "text/plain")},
        )

    assert response.status_code == 415
    assert response.json()["code"] == "unsupported_pdf"


@pytest.mark.asyncio
async def test_resume_upload_rejects_malformed_pdf() -> None:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/resume/upload",
            files={"file": ("resume.pdf", b"not a pdf", "application/pdf")},
        )

    assert response.status_code == 422
    assert response.json()["code"] == "pdf_parsing_error"
