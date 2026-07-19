import math
import re

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ResourceNotFoundError
from app.models.analysis_record import AnalysisRecord
from app.models.chat_history import ChatHistory
from app.models.resume import Resume
from app.schemas.history import (
    AnalysisHistoryDetail,
    AnalysisHistoryItem,
    AnalysisHistoryPage,
    ChatHistoryItem,
    ChatHistoryPage,
    ResumeHistoryItem,
    ResumeHistoryPage,
)
from app.schemas.resume import ResumeAnalysisResponse


def _page_count(total: int, page_size: int) -> int:
    return math.ceil(total / page_size) if total else 0


def _job_summary(job_description: str | None) -> tuple[str, str]:
    if not job_description:
        return "未记录岗位信息", "该历史记录创建于岗位信息持久化功能上线之前。"
    normalized = re.sub(r"\s+", " ", job_description).strip()
    first_line = next(
        (line.strip() for line in job_description.splitlines() if line.strip()),
        normalized,
    )
    title = first_line[:120]
    preview = normalized[:240] + ("…" if len(normalized) > 240 else "")
    return title, preview


async def list_resumes(
    session: AsyncSession,
    user_id: int,
    page: int,
    page_size: int,
) -> ResumeHistoryPage:
    total = int(
        await session.scalar(
            select(func.count()).select_from(Resume).where(Resume.user_id == user_id)
        )
        or 0
    )
    analysis_count = (
        select(func.count(AnalysisRecord.id))
        .where(AnalysisRecord.resume_id == Resume.id)
        .correlate(Resume)
        .scalar_subquery()
    )
    statement = (
        select(Resume, analysis_count)
        .where(Resume.user_id == user_id)
        .order_by(Resume.create_time.desc(), Resume.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    rows = (await session.execute(statement)).all()
    return ResumeHistoryPage(
        items=[
            ResumeHistoryItem(
                id=resume.id,
                filename=resume.filename,
                analysis_count=int(analysis_count),
                created_at=resume.create_time,
            )
            for resume, analysis_count in rows
        ],
        total=total,
        page=page,
        page_size=page_size,
        pages=_page_count(total, page_size),
    )


def _analysis_item(record: AnalysisRecord, resume: Resume) -> AnalysisHistoryItem:
    title, preview = _job_summary(record.job_description)
    return AnalysisHistoryItem(
        id=record.id,
        resume_id=resume.id,
        resume_filename=resume.filename,
        score=record.score,
        job_title=title,
        job_description_preview=preview,
        created_at=record.create_time,
    )


async def list_analyses(
    session: AsyncSession,
    user_id: int,
    page: int,
    page_size: int,
) -> AnalysisHistoryPage:
    owned = (
        select(AnalysisRecord.id)
        .join(Resume, Resume.id == AnalysisRecord.resume_id)
        .where(Resume.user_id == user_id)
        .subquery()
    )
    total = int(await session.scalar(select(func.count()).select_from(owned)) or 0)
    statement = (
        select(AnalysisRecord, Resume)
        .join(Resume, Resume.id == AnalysisRecord.resume_id)
        .where(Resume.user_id == user_id)
        .order_by(AnalysisRecord.create_time.desc(), AnalysisRecord.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    rows = (await session.execute(statement)).all()
    return AnalysisHistoryPage(
        items=[_analysis_item(record, resume) for record, resume in rows],
        total=total,
        page=page,
        page_size=page_size,
        pages=_page_count(total, page_size),
    )


async def get_analysis_detail(
    session: AsyncSession,
    user_id: int,
    analysis_id: int,
) -> AnalysisHistoryDetail:
    statement = (
        select(AnalysisRecord, Resume)
        .join(Resume, Resume.id == AnalysisRecord.resume_id)
        .where(AnalysisRecord.id == analysis_id, Resume.user_id == user_id)
    )
    row = (await session.execute(statement)).one_or_none()
    if row is None:
        raise ResourceNotFoundError
    record, resume = row
    item = _analysis_item(record, resume)
    return AnalysisHistoryDetail(
        **item.model_dump(),
        job_description=record.job_description,
        result=ResumeAnalysisResponse.model_validate(record.result_json),
    )


async def list_chats(
    session: AsyncSession,
    user_id: int,
    chat_type: str,
    page: int,
    page_size: int,
) -> ChatHistoryPage:
    filters = (ChatHistory.user_id == user_id, ChatHistory.chat_type == chat_type)
    total = int(
        await session.scalar(
            select(func.count()).select_from(ChatHistory).where(*filters)
        )
        or 0
    )
    statement = (
        select(ChatHistory)
        .where(*filters)
        .order_by(ChatHistory.time.desc(), ChatHistory.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    histories = (await session.scalars(statement)).all()
    return ChatHistoryPage(
        items=[
            ChatHistoryItem(
                id=history.id,
                question=history.question,
                answer=history.answer,
                sources=history.sources_json or [],
                created_at=history.time,
            )
            for history in histories
        ],
        total=total,
        page=page,
        page_size=page_size,
        pages=_page_count(total, page_size),
    )
