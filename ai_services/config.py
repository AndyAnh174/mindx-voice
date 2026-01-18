"""
AI Services Configuration.

Environment variables for AI providers.
"""

import os
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class GeminiConfig:
    """Configuration for Google Gemini API."""
    
    api_key: str = field(default_factory=lambda: os.getenv("GEMINI_API_KEY", ""))
    model: str = field(default_factory=lambda: os.getenv("GEMINI_MODEL", "gemini-2.0-flash"))
    
    # Generation parameters
    max_output_tokens: int = 2048
    temperature: float = 0.7
    top_p: float = 0.95
    top_k: int = 40
    
    # Timeout and retry settings
    timeout: int = 30  # seconds
    max_retries: int = 3
    retry_min_wait: float = 1.0  # seconds
    retry_max_wait: float = 10.0  # seconds
    
    # Safety settings
    block_dangerous_content: bool = True
    
    def validate(self) -> bool:
        """Check if configuration is valid."""
        return bool(self.api_key)


@dataclass
class WhisperConfig:
    """Configuration for OpenAI Whisper STT API."""
    
    api_key: str = field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    model: str = field(default_factory=lambda: os.getenv("WHISPER_MODEL", "whisper-1"))
    
    # Audio settings
    supported_formats: tuple = ("mp3", "mp4", "mpeg", "mpga", "m4a", "wav", "webm", "ogg", "flac")
    max_file_size_mb: int = 25  # OpenAI limit
    default_language: str = "vi"  # Vietnamese
    
    # Transcription parameters
    response_format: str = "json"  # json, text, srt, verbose_json, vtt
    
    # Timeout and retry settings
    timeout: int = 60  # seconds - audio transcription can be slow
    max_retries: int = 3
    retry_min_wait: float = 2.0  # seconds
    retry_max_wait: float = 30.0  # seconds
    
    # Sample rate for audio normalization
    target_sample_rate: int = 16000  # Whisper optimal sample rate
    
    def validate(self) -> bool:
        """Check if configuration is valid."""
        return bool(self.api_key)
    
    def is_supported_format(self, filename: str) -> bool:
        """Check if audio format is supported."""
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        return ext in self.supported_formats


@dataclass
class AIServiceConfig:
    """Main AI service configuration."""
    
    gemini: GeminiConfig = field(default_factory=GeminiConfig)
    whisper: WhisperConfig = field(default_factory=WhisperConfig)
    
    # Default provider
    default_provider: str = "gemini"
    
    # Logging
    log_requests: bool = True
    log_responses: bool = True
    
    @classmethod
    def from_env(cls) -> "AIServiceConfig":
        """Create config from environment variables."""
        return cls(
            gemini=GeminiConfig(),
            whisper=WhisperConfig(),
            default_provider=os.getenv("AI_PROVIDER", "gemini"),
            log_requests=os.getenv("AI_LOG_REQUESTS", "true").lower() == "true",
            log_responses=os.getenv("AI_LOG_RESPONSES", "true").lower() == "true",
        )


# Global config instance
ai_config = AIServiceConfig.from_env()

