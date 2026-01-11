"""
Custom exceptions for AI services.
"""


class AIServiceError(Exception):
    """Base exception for AI service errors."""
    
    def __init__(self, message: str, code: str = "AI_ERROR", details: dict = None):
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details or {}
    
    def to_dict(self) -> dict:
        """Convert to dictionary for API response."""
        return {
            "error": {
                "code": self.code,
                "message": self.message,
                "details": self.details,
            }
        }


class APIKeyError(AIServiceError):
    """API key missing or invalid."""
    
    def __init__(self, message: str = "API key không hợp lệ hoặc chưa được cấu hình."):
        super().__init__(message, code="API_KEY_ERROR")


class RateLimitError(AIServiceError):
    """Rate limit exceeded."""
    
    def __init__(self, message: str = "Đã vượt quá giới hạn request. Vui lòng thử lại sau."):
        super().__init__(message, code="RATE_LIMIT_ERROR")


class QuotaExceededError(AIServiceError):
    """API quota exceeded."""
    
    def __init__(self, message: str = "Đã hết quota API. Vui lòng liên hệ admin."):
        super().__init__(message, code="QUOTA_EXCEEDED")


class ModelError(AIServiceError):
    """Model-related error (invalid model, model unavailable, etc.)."""
    
    def __init__(self, message: str = "Lỗi model AI. Vui lòng thử lại sau."):
        super().__init__(message, code="MODEL_ERROR")


class ContentFilterError(AIServiceError):
    """Content blocked by safety filters."""
    
    def __init__(self, message: str = "Nội dung bị chặn bởi bộ lọc an toàn."):
        super().__init__(message, code="CONTENT_FILTERED")


class TimeoutError(AIServiceError):
    """Request timeout."""
    
    def __init__(self, message: str = "Request đã hết thời gian chờ. Vui lòng thử lại."):
        super().__init__(message, code="TIMEOUT_ERROR")


class NetworkError(AIServiceError):
    """Network connectivity error."""
    
    def __init__(self, message: str = "Lỗi kết nối mạng. Vui lòng kiểm tra kết nối."):
        super().__init__(message, code="NETWORK_ERROR")


class InvalidRequestError(AIServiceError):
    """Invalid request parameters."""
    
    def __init__(self, message: str = "Request không hợp lệ.", details: dict = None):
        super().__init__(message, code="INVALID_REQUEST", details=details)


class GenerationError(AIServiceError):
    """Error during content generation."""
    
    def __init__(self, message: str = "Lỗi trong quá trình tạo nội dung.", details: dict = None):
        super().__init__(message, code="GENERATION_ERROR", details=details)
