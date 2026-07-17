from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, File, UploadFile, status
from starlette.concurrency import run_in_threadpool

from app.core.exceptions import PDFTooLargeError, UnsupportedPDFError
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


@router.post(
    "/upload",
    response_model=ResumeUploadResponse,
    status_code=status.HTTP_200_OK,
    summary="Upload and extract text from a PDF resume",
)
async def upload_resume(
    file: Annotated[UploadFile, File(description="PDF resume, up to 10 MB")],
    parser: Annotated[PDFParserService, Depends(get_pdf_parser_service)],
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
    return ResumeUploadResponse(
        filename=parsed.filename,
        text=parsed.text,
        pages=parsed.pages,
    )
