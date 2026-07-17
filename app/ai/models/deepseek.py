from langchain_core.language_models.chat_models import BaseChatModel
from langchain_deepseek import ChatDeepSeek

from app.core.config import Settings, get_settings
from app.core.exceptions import LLMConfigurationError


def create_deepseek_model(settings: Settings | None = None) -> BaseChatModel:
    """Build the DeepSeek LangChain model from environment-backed settings."""
    resolved_settings = settings or get_settings()
    api_key = resolved_settings.deepseek_api_key.get_secret_value().strip()
    if not api_key:
        raise LLMConfigurationError

    try:
        return ChatDeepSeek(
            model=resolved_settings.deepseek_model,
            api_key=resolved_settings.deepseek_api_key,
            temperature=resolved_settings.deepseek_temperature,
            max_tokens=resolved_settings.deepseek_max_tokens,
            timeout=resolved_settings.deepseek_timeout_seconds,
            max_retries=resolved_settings.deepseek_max_retries,
        )
    except Exception as exc:
        raise LLMConfigurationError from exc
