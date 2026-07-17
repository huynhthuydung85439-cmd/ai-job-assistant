from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, File, UploadFile, status

from app.core.exceptions import PDFTooLargeError, UnsupportedPDFError
from app.rag.rag_service import RAGService, get_rag_service
from app.schemas.knowledge import (
    KnowledgeChatRequest,
    KnowledgeChatResponse,
    KnowledgeUploadResponse,
)
from app.services.pdf_parser import MAX_PDF_SIZE_BYTES

router = APIRouter(prefix="/knowledge")


@router.post(
    "/upload",
    response_model=KnowledgeUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a PDF to the knowledge base",
)
async def upload_knowledge(
    file: Annotated[UploadFile, File(description="PDF knowledge file, up to 10 MB")],
    service: Annotated[RAGService, Depends(get_rag_service)],
) -> KnowledgeUploadResponse:
    filename = Path((file.filename or "knowledge.pdf").replace("\\", "/")).name
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

    loaded = await service.upload_pdf(filename=filename, content=content)
    return KnowledgeUploadResponse(
        document_id=loaded.document_id,
        filename=loaded.filename,
        pages=loaded.pages,
        chunks=len(loaded.chunks),
    )


@router.post(
    "/chat",
    response_model=KnowledgeChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Answer a question using the knowledge base",
)
async def chat_with_knowledge(
    payload: KnowledgeChatRequest,
    service: Annotated[RAGService, Depends(get_rag_service)],
) -> KnowledgeChatResponse:
    answer, sources = await service.answer(payload.question)
    return KnowledgeChatResponse(answer=answer, sources=sources)
