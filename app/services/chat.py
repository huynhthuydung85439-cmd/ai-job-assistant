from __future__ import annotations

import logging
from functools import lru_cache
from typing import TYPE_CHECKING

from app.core.exceptions import ApplicationError, LLMServiceError

if TYPE_CHECKING:
    from langchain_core.language_models.chat_models import BaseChatModel
    from langchain_core.runnables import Runnable

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """你是一个专业、客观的 AI 求职助手。
请根据用户提供的信息回答求职、岗位、简历和面试相关问题。
信息不足时应明确说明，并提出需要补充的关键信息。"""


class ChatService:
    def __init__(self, model: BaseChatModel) -> None:
        from langchain_core.output_parsers import StrOutputParser
        from langchain_core.prompts import ChatPromptTemplate

        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", SYSTEM_PROMPT),
                ("human", "{message}"),
            ]
        )
        self._chain: Runnable[dict[str, str], str] = prompt | model | StrOutputParser()

    async def chat(self, message: str) -> str:
        try:
            answer = await self._chain.ainvoke({"message": message})
        except ApplicationError:
            raise
        except Exception as exc:
            logger.exception("DeepSeek chat request failed")
            raise LLMServiceError from exc

        answer = answer.strip()
        if not answer:
            logger.error("DeepSeek returned an empty chat response")
            raise LLMServiceError
        return answer


@lru_cache
def get_chat_service() -> ChatService:
    from app.ai.models.deepseek import create_deepseek_model

    return ChatService(create_deepseek_model())
