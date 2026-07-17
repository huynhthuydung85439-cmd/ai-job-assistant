from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ResourceAccessDeniedError, ResourceNotFoundError
from app.models.analysis_record import AnalysisRecord
from app.models.chat_history import ChatHistory
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
) -> ChatHistory:
    history = ChatHistory(user_id=user_id, question=question, answer=answer)
    session.add(history)
    await session.commit()
    await session.refresh(history)
    return history
