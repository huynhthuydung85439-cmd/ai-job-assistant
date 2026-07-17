from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat import ChatService, get_chat_service

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
) -> ChatResponse:
    answer = await service.chat(payload.message)
    return ChatResponse(answer=answer)
