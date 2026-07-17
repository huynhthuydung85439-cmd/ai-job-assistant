import pytest
from langchain_core.language_models import FakeListChatModel

from app.ai.models.deepseek import create_deepseek_model
from app.core.config import Settings
from app.core.exceptions import LLMConfigurationError
from app.services.chat import ChatService


@pytest.mark.asyncio
async def test_chat_service_uses_langchain_model() -> None:
    service = ChatService(FakeListChatModel(responses=["岗位匹配度较高。"]))

    answer = await service.chat("分析这个岗位")

    assert answer == "岗位匹配度较高。"


def test_deepseek_model_requires_api_key() -> None:
    settings = Settings(_env_file=None, deepseek_api_key="")

    with pytest.raises(LLMConfigurationError):
        create_deepseek_model(settings)
