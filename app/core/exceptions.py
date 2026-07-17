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
