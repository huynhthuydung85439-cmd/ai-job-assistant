class ApplicationError(Exception):
    """Base class for errors that are safe to expose through the API."""

    status_code = 500
    error_code = "application_error"
    headers: dict[str, str] | None = None
    public_message = "服务暂时不可用，请稍后重试。"


class LLMConfigurationError(ApplicationError):
    status_code = 503
    error_code = "llm_not_configured"
    public_message = "大模型服务尚未正确配置。"


class LLMServiceError(ApplicationError):
    status_code = 502
    error_code = "llm_service_error"
    public_message = "大模型服务暂时不可用，请稍后重试。"


class UnsupportedPDFError(ApplicationError):
    status_code = 415
    error_code = "unsupported_pdf"
    public_message = "仅支持上传 PDF 文件。"


class PDFTooLargeError(ApplicationError):
    status_code = 413
    error_code = "pdf_too_large"
    public_message = "PDF 文件不能超过 10 MB。"


class PDFParsingError(ApplicationError):
    status_code = 422
    error_code = "pdf_parsing_error"
    public_message = "PDF 无法解析或未包含可提取的文本。"


class KnowledgeBaseError(ApplicationError):
    status_code = 503
    error_code = "knowledge_base_error"
    public_message = "知识库服务暂时不可用，请稍后重试。"


class AuthConfigurationError(ApplicationError):
    status_code = 503
    error_code = "auth_not_configured"
    public_message = "认证服务尚未正确配置。"


class AuthenticationError(ApplicationError):
    status_code = 401
    error_code = "authentication_failed"
    public_message = "用户名、密码或访问令牌无效。"
    headers = {"WWW-Authenticate": "Bearer"}


class DuplicateUserError(ApplicationError):
    status_code = 409
    error_code = "user_already_exists"
    public_message = "用户名或邮箱已被注册。"


class PasswordPolicyError(ApplicationError):
    status_code = 422
    error_code = "invalid_password"
    public_message = "密码必须为 8 至 72 个字节。"


class ResourceNotFoundError(ApplicationError):
    status_code = 404
    error_code = "resource_not_found"
    public_message = "请求的资源不存在。"


class ResourceAccessDeniedError(ApplicationError):
    status_code = 403
    error_code = "resource_access_denied"
    public_message = "无权访问该资源。"
