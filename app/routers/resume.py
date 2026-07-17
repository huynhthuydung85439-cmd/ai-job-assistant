from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.schemas.resume import ResumeAnalysisRequest, ResumeAnalysisResponse
from app.services.resume_analyzer import ResumeAnalyzerService, get_resume_analyzer_service

router = APIRouter(prefix="/resume")


@router.post(
    "/analyze",
    response_model=ResumeAnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Analyze a resume against a target job description",
)
async def analyze_resume(
    payload: ResumeAnalysisRequest,
    service: Annotated[ResumeAnalyzerService, Depends(get_resume_analyzer_service)],
) -> ResumeAnalysisResponse:
    return await service.analyze(
        resume_text=payload.resume_text,
        job_description=payload.job_description,
    )
