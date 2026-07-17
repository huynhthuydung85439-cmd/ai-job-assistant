class ApplicationError(Exception):
    """Base class for errors that are safe to expose through the API."""

    status_code = 500
    error_code = "application_error"
    public_message = "服务暂时不可用，请稍后重试。"


class LLMConfigurationError(ApplicationError):
    status_code = 503
    error_code = "llm_not_configured"
    public_message = "大模型服务尚未正确配置。"


class LLMServiceError(ApplicationError):
    status_code = 502
    error_code = "llm_service_error"
    public_message = "大模型服务暂时不可用，请稍后重试。"
