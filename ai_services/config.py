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
class AIServiceConfig:
    """Main AI service configuration."""
    
    gemini: GeminiConfig = field(default_factory=GeminiConfig)
    
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
            default_provider=os.getenv("AI_PROVIDER", "gemini"),
            log_requests=os.getenv("AI_LOG_REQUESTS", "true").lower() == "true",
            log_responses=os.getenv("AI_LOG_RESPONSES", "true").lower() == "true",
        )


# Global config instance
ai_config = AIServiceConfig.from_env()
