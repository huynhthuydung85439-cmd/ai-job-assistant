import httpx
import pytest

from app.core.exceptions import LLMServiceError
from app.main import app
from app.services.chat import get_chat_service


class SuccessfulChatService:
    async def chat(self, message: str) -> str:
        assert message == "帮我分析这个岗位"
        return "请提供岗位描述，我会从职责、要求和匹配度进行分析。"


class FailingChatService:
    async def chat(self, _: str) -> str:
        raise LLMServiceError


async def post_chat(payload: dict[str, str]) -> httpx.Response:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.post("/api/v1/chat", json=payload)


@pytest.mark.asyncio
async def test_chat_returns_model_answer() -> None:
    app.dependency_overrides[get_chat_service] = SuccessfulChatService
    try:
        response = await post_chat({"message": "帮我分析这个岗位"})
    finally:
        app.dependency_overrides.pop(get_chat_service, None)

    assert response.status_code == 200
    assert response.json() == {"answer": "请提供岗位描述，我会从职责、要求和匹配度进行分析。"}


@pytest.mark.asyncio
async def test_chat_rejects_blank_message() -> None:
    app.dependency_overrides[get_chat_service] = SuccessfulChatService
    try:
        response = await post_chat({"message": "   "})
    finally:
        app.dependency_overrides.pop(get_chat_service, None)

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_chat_handles_provider_failure() -> None:
    app.dependency_overrides[get_chat_service] = FailingChatService
    try:
        response = await post_chat({"message": "帮我分析这个岗位"})
    finally:
        app.dependency_overrides.pop(get_chat_service, None)

    assert response.status_code == 502
    assert response.json() == {
        "detail": "大模型服务暂时不可用，请稍后重试。",
        "code": "llm_service_error",
    }
