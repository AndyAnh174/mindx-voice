"""
AI Services Package.

Provides AI integration for the Voice Chat application.
"""

from .config import ai_config, GeminiConfig, AIServiceConfig
from .exceptions import (
    AIServiceError,
    APIKeyError,
    RateLimitError,
    QuotaExceededError,
    ModelError,
    ContentFilterError,
    TimeoutError,
    NetworkError,
    InvalidRequestError,
    GenerationError,
)
from .models import (
    ChatMessage,
    MessageRole,
    PersonaContext,
    GenerationParams,
    GenerationRequest,
    GenerationResponse,
    StreamChunk,
)
from .gemini_service import (
    GeminiService,
    gemini_service,
    generate_reply,
    generate_reply_stream,
)


__all__ = [
    # Config
    "ai_config",
    "GeminiConfig",
    "AIServiceConfig",
    
    # Exceptions
    "AIServiceError",
    "APIKeyError",
    "RateLimitError",
    "QuotaExceededError",
    "ModelError",
    "ContentFilterError",
    "TimeoutError",
    "NetworkError",
    "InvalidRequestError",
    "GenerationError",
    
    # Models
    "ChatMessage",
    "MessageRole",
    "PersonaContext",
    "GenerationParams",
    "GenerationRequest",
    "GenerationResponse",
    "StreamChunk",
    
    # Services
    "GeminiService",
    "gemini_service",
    "generate_reply",
    "generate_reply_stream",
]
