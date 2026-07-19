from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.history import (
    AnalysisHistoryDetail,
    AnalysisHistoryPage,
    ChatHistoryPage,
    ResumeHistoryPage,
)
from app.services.history import (
    get_analysis_detail,
    list_analyses,
    list_chats,
    list_resumes,
)

router = APIRouter(prefix="/history")

Page = Annotated[int, Query(ge=1)]
PageSize = Annotated[int, Query(ge=1, le=100)]


@router.get(
    "/resumes",
    response_model=ResumeHistoryPage,
    status_code=status.HTTP_200_OK,
    summary="List the current user's resumes",
)
async def resume_history(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    page: Page = 1,
    page_size: PageSize = 20,
) -> ResumeHistoryPage:
    return await list_resumes(session, current_user.id, page, page_size)


@router.get(
    "/analyses",
    response_model=AnalysisHistoryPage,
    status_code=status.HTTP_200_OK,
    summary="List the current user's resume analyses",
)
async def analysis_history(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    page: Page = 1,
    page_size: PageSize = 20,
) -> AnalysisHistoryPage:
    return await list_analyses(session, current_user.id, page, page_size)


@router.get(
    "/analyses/{analysis_id}",
    response_model=AnalysisHistoryDetail,
    status_code=status.HTTP_200_OK,
    summary="Get one resume analysis owned by the current user",
)
async def analysis_history_detail(
    analysis_id: Annotated[int, Path(gt=0)],
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> AnalysisHistoryDetail:
    return await get_analysis_detail(session, current_user.id, analysis_id)


@router.get(
    "/chats",
    response_model=ChatHistoryPage,
    status_code=status.HTTP_200_OK,
    summary="List the current user's ordinary AI chats",
)
async def chat_history(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    page: Page = 1,
    page_size: PageSize = 20,
) -> ChatHistoryPage:
    return await list_chats(session, current_user.id, "chat", page, page_size)


@router.get(
    "/rag-chats",
    response_model=ChatHistoryPage,
    status_code=status.HTTP_200_OK,
    summary="List the current user's RAG question history",
)
async def rag_chat_history(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    page: Page = 1,
    page_size: PageSize = 20,
) -> ChatHistoryPage:
    return await list_chats(session, current_user.id, "rag", page, page_size)
