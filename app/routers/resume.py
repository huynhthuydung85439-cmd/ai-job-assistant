from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, File, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.concurrency import run_in_threadpool

from app.core.exceptions import AuthenticationError, PDFTooLargeError, UnsupportedPDFError
from app.db.session import get_db_session
from app.dependencies.auth import get_optional_current_user
from app.models.user import User
from app.schemas.resume import (
    ResumeAnalysisRequest,
    ResumeAnalysisResponse,
    ResumeUploadResponse,
)
from app.services.pdf_parser import (
    MAX_PDF_SIZE_BYTES,
    PDFParserService,
    get_pdf_parser_service,
)
from app.services.records import save_analysis, save_resume
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
    session: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User | None, Depends(get_optional_current_user)],
) -> ResumeAnalysisResponse:
    if payload.resume_id is not None and current_user is None:
        raise AuthenticationError

    result = await service.analyze(
        resume_text=payload.resume_text,
        job_description=payload.job_description,
    )
    if payload.resume_id is not None and current_user is not None:
        await save_analysis(
            session=session,
            user_id=current_user.id,
            resume_id=payload.resume_id,
            score=result.score,
            result_json=result.model_dump(),
        )
    return result


@router.post(
    "/upload",
    response_model=ResumeUploadResponse,
    response_model_exclude_none=True,
    status_code=status.HTTP_200_OK,
    summary="Upload and extract text from a PDF resume",
)
async def upload_resume(
    file: Annotated[UploadFile, File(description="PDF resume, up to 10 MB")],
    parser: Annotated[PDFParserService, Depends(get_pdf_parser_service)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User | None, Depends(get_optional_current_user)],
) -> ResumeUploadResponse:
    filename = Path((file.filename or "resume.pdf").replace("\\", "/")).name
    content_type = (file.content_type or "").lower()
    if not filename.lower().endswith(".pdf") or content_type not in {
        "application/pdf",
        "application/x-pdf",
    }:
        await file.close()
        raise UnsupportedPDFError

    try:
        content = await file.read(MAX_PDF_SIZE_BYTES + 1)
    finally:
        await file.close()

    if len(content) > MAX_PDF_SIZE_BYTES:
        raise PDFTooLargeError

    parsed = await run_in_threadpool(parser.parse, filename, content)
    resume_id = None
    if current_user is not None:
        resume = await save_resume(
            session=session,
            user_id=current_user.id,
            filename=parsed.filename,
            content=parsed.text,
        )
        resume_id = resume.id
    return ResumeUploadResponse(
        filename=parsed.filename,
        text=parsed.text,
        pages=parsed.pages,
        resume_id=resume_id,
    )
