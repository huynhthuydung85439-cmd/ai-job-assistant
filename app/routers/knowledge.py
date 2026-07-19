import math
from pathlib import Path
from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    File,
    Query,
    UploadFile,
    status,
)
from fastapi import (
    Path as ApiPath,
)
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.exceptions import (
    PDFTooLargeError,
    ResourceNotFoundError,
    UnsupportedPDFError,
)
from app.db.session import get_db_session
from app.dependencies.auth import get_current_user
from app.models.knowledge_document import KnowledgeDocument
from app.models.user import User
from app.rag.rag_service import RAGService, get_rag_service
from app.schemas.knowledge import (
    KnowledgeChatRequest,
    KnowledgeChatResponse,
    KnowledgeDeleteResponse,
    KnowledgeDocumentItem,
    KnowledgeDocumentPage,
    KnowledgeUploadResponse,
    KnowledgeWarmupResponse,
)
from app.services.pdf_parser import MAX_PDF_SIZE_BYTES
from app.services.records import save_chat_history, save_knowledge_document

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
    session: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(get_current_user)],
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

    loaded = await service.upload_pdf(
        filename=filename,
        content=content,
        user_id=current_user.id,
    )
    vector_ids = [str(chunk.id) for chunk in loaded.chunks if chunk.id is not None]
    try:
        document = await save_knowledge_document(
            session=session,
            document_id=loaded.document_id,
            user_id=current_user.id,
            filename=loaded.filename,
            pages=loaded.pages,
            chunk_count=len(loaded.chunks),
            collection_name=service.collection_name,
            vector_ids=vector_ids,
        )
    except Exception:
        await session.rollback()
        await service.delete_chunks(vector_ids)
        raise
    return KnowledgeUploadResponse(
        document_id=document.id,
        filename=document.filename,
        pages=document.pages,
        chunks=document.chunk_count,
        collection_name=document.collection_name,
        uploaded_at=document.create_time,
    )


@router.get(
    "/documents",
    response_model=KnowledgeDocumentPage,
    status_code=status.HTTP_200_OK,
    summary="List the current user's knowledge documents",
)
async def list_knowledge_documents(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> KnowledgeDocumentPage:
    filters = (KnowledgeDocument.user_id == current_user.id,)
    total = int(
        await session.scalar(
            select(func.count()).select_from(KnowledgeDocument).where(*filters)
        )
        or 0
    )
    statement = (
        select(KnowledgeDocument)
        .where(*filters)
        .order_by(KnowledgeDocument.create_time.desc(), KnowledgeDocument.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    documents = (await session.scalars(statement)).all()
    return KnowledgeDocumentPage(
        items=[
            KnowledgeDocumentItem(
                document_id=document.id,
                filename=document.filename,
                pages=document.pages,
                chunks=document.chunk_count,
                collection_name=document.collection_name,
                uploaded_at=document.create_time,
            )
            for document in documents
        ],
        total=total,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size) if total else 0,
    )


@router.delete(
    "/documents/{document_id}",
    response_model=KnowledgeDeleteResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete a knowledge document and its vectors",
)
async def delete_knowledge_document(
    document_id: Annotated[str, ApiPath(min_length=1, max_length=36)],
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    service: Annotated[RAGService, Depends(get_rag_service)],
) -> KnowledgeDeleteResponse:
    document = await session.scalar(
        select(KnowledgeDocument).where(
            KnowledgeDocument.id == document_id,
            KnowledgeDocument.user_id == current_user.id,
        )
    )
    if document is None:
        raise ResourceNotFoundError
    await service.delete_chunks(document.vector_ids)
    await session.delete(document)
    await session.commit()
    return KnowledgeDeleteResponse(document_id=document_id, deleted=True)


@router.post(
    "/warmup",
    response_model=KnowledgeWarmupResponse,
    status_code=status.HTTP_200_OK,
    summary="Warm up the authenticated user's knowledge embedding service",
)
async def warmup_knowledge(
    _: Annotated[User, Depends(get_current_user)],
    service: Annotated[RAGService, Depends(get_rag_service)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> KnowledgeWarmupResponse:
    await service.warmup()
    return KnowledgeWarmupResponse(status="ready", model=settings.embedding_model)


@router.post(
    "/chat",
    response_model=KnowledgeChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Answer a question using the knowledge base",
)
async def chat_with_knowledge(
    payload: KnowledgeChatRequest,
    service: Annotated[RAGService, Depends(get_rag_service)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> KnowledgeChatResponse:
    answer, sources = await service.answer(payload.question, current_user.id)
    await save_chat_history(
        session=session,
        user_id=current_user.id,
        question=payload.question,
        answer=answer,
        chat_type="rag",
        sources=sources,
    )
    return KnowledgeChatResponse(answer=answer, sources=sources)
