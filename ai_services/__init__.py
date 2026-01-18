"""
AI Services Package.

Provides AI integration for the Voice Chat application.
"""

from .config import ai_config, GeminiConfig, WhisperConfig, AIServiceConfig
from .exceptions import (
    AIServiceError,
    AIServiceConfigError,
    APIKeyError,
    RateLimitError,
    AIServiceRateLimitError,
    QuotaExceededError,
    ModelError,
    ContentFilterError,
    TimeoutError,
    AIServiceTimeoutError,
    NetworkError,
    InvalidRequestError,
    GenerationError,
    AudioProcessingError,
    TranscriptionError,
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
from .whisper_service import (
    WhisperService,
    TranscriptionResult,
    TranscriptionMetrics,
    AudioMetadata,
    get_whisper_service,
    transcribe_audio,
)


__all__ = [
    # Config
    "ai_config",
    "GeminiConfig",
    "WhisperConfig",
    "AIServiceConfig",
    
    # Exceptions
    "AIServiceError",
    "AIServiceConfigError",
    "APIKeyError",
    "RateLimitError",
    "AIServiceRateLimitError",
    "QuotaExceededError",
    "ModelError",
    "ContentFilterError",
    "TimeoutError",
    "AIServiceTimeoutError",
    "NetworkError",
    "InvalidRequestError",
    "GenerationError",
    "AudioProcessingError",
    "TranscriptionError",
    
    # Models
    "ChatMessage",
    "MessageRole",
    "PersonaContext",
    "GenerationParams",
    "GenerationRequest",
    "GenerationResponse",
    "StreamChunk",
    
    # Gemini Service
    "GeminiService",
    "gemini_service",
    "generate_reply",
    "generate_reply_stream",
    
    # Whisper Service
    "WhisperService",
    "TranscriptionResult",
    "TranscriptionMetrics",
    "AudioMetadata",
    "get_whisper_service",
    "transcribe_audio",
]

