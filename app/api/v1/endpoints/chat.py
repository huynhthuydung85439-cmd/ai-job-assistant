from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.dependencies.auth import get_optional_current_user
from app.models.user import User
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat import ChatService, get_chat_service
from app.services.records import save_chat_history

router = APIRouter()


@router.post(
    "/chat",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Chat with the AI job assistant",
)
async def chat(
    payload: ChatRequest,
    service: Annotated[ChatService, Depends(get_chat_service)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User | None, Depends(get_optional_current_user)],
) -> ChatResponse:
    answer = await service.chat(payload.message)
    if current_user is not None:
        await save_chat_history(
            session=session,
            user_id=current_user.id,
            question=payload.message,
            answer=answer,
            chat_type="chat",
        )
    return ChatResponse(answer=answer)
