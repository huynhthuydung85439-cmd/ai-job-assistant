from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ResourceAccessDeniedError, ResourceNotFoundError
from app.models.analysis_record import AnalysisRecord
from app.models.chat_history import ChatHistory
from app.models.knowledge_document import KnowledgeDocument
from app.models.resume import Resume


async def save_resume(
    session: AsyncSession,
    user_id: int,
    filename: str,
    content: str,
) -> Resume:
    resume = Resume(user_id=user_id, filename=filename, content=content)
    session.add(resume)
    await session.commit()
    await session.refresh(resume)
    return resume


async def save_analysis(
    session: AsyncSession,
    user_id: int,
    resume_id: int,
    score: int,
    result_json: dict[str, Any],
    job_description: str,
) -> AnalysisRecord:
    resume = await session.get(Resume, resume_id)
    if resume is None:
        raise ResourceNotFoundError
    if resume.user_id != user_id:
        raise ResourceAccessDeniedError

    record = AnalysisRecord(
        resume_id=resume_id,
        score=score,
        result_json=result_json,
        job_description=job_description,
    )
    session.add(record)
    await session.commit()
    await session.refresh(record)
    return record


async def save_chat_history(
    session: AsyncSession,
    user_id: int,
    question: str,
    answer: str,
    chat_type: str = "chat",
    sources: list[str] | None = None,
) -> ChatHistory:
    history = ChatHistory(
        user_id=user_id,
        question=question,
        answer=answer,
        chat_type=chat_type,
        sources_json=sources,
    )
    session.add(history)
    await session.commit()
    await session.refresh(history)
    return history


async def save_knowledge_document(
    session: AsyncSession,
    *,
    document_id: str,
    user_id: int,
    filename: str,
    pages: int,
    chunk_count: int,
    collection_name: str,
    vector_ids: list[str],
) -> KnowledgeDocument:
    document = KnowledgeDocument(
        id=document_id,
        user_id=user_id,
        filename=filename,
        pages=pages,
        chunk_count=chunk_count,
        collection_name=collection_name,
        vector_ids=vector_ids,
    )
    session.add(document)
    await session.commit()
    await session.refresh(document)
    return document
