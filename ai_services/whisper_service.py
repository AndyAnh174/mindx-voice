"""
Whisper STT Service.

Speech-to-Text service using OpenAI Whisper API with:
- Retry logic with exponential backoff
- Audio format validation and normalization
- Comprehensive logging and metrics
"""

import io
import time
import logging
from typing import Optional, BinaryIO, Union
from dataclasses import dataclass, field
from datetime import datetime

import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)

from .config import ai_config, WhisperConfig
from .exceptions import (
    AIServiceError,
    AIServiceConfigError,
    AIServiceRateLimitError,
    AIServiceTimeoutError,
)


logger = logging.getLogger(__name__)


# ===================== AUDIO UTILS =====================

@dataclass
class AudioMetadata:
    """Metadata about an audio file."""
    filename: str
    size_bytes: int
    format: str
    duration_seconds: Optional[float] = None
    sample_rate: Optional[int] = None
    channels: Optional[int] = None


def get_audio_format(filename: str) -> str:
    """Extract audio format from filename."""
    if "." not in filename:
        return ""
    return filename.rsplit(".", 1)[-1].lower()


def validate_audio_file(
    file_data: bytes,
    filename: str,
    config: WhisperConfig
) -> AudioMetadata:
    """
    Validate audio file against Whisper requirements.
    
    Args:
        file_data: Raw audio file bytes
        filename: Original filename
        config: Whisper configuration
        
    Returns:
        AudioMetadata with file info
        
    Raises:
        AIServiceError: If validation fails
    """
    # Check format
    audio_format = get_audio_format(filename)
    if not config.is_supported_format(filename):
        raise AIServiceError(
            f"Unsupported audio format: {audio_format}. "
            f"Supported formats: {', '.join(config.supported_formats)}"
        )
    
    # Check file size
    size_bytes = len(file_data)
    max_bytes = config.max_file_size_mb * 1024 * 1024
    if size_bytes > max_bytes:
        raise AIServiceError(
            f"Audio file too large: {size_bytes / 1024 / 1024:.1f}MB. "
            f"Maximum allowed: {config.max_file_size_mb}MB"
        )
    
    if size_bytes == 0:
        raise AIServiceError("Audio file is empty")
    
    return AudioMetadata(
        filename=filename,
        size_bytes=size_bytes,
        format=audio_format,
    )


# ===================== METRICS =====================

@dataclass
class TranscriptionMetrics:
    """Metrics for a transcription request."""
    request_id: str = ""
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    duration_ms: float = 0
    audio_size_bytes: int = 0
    audio_duration_seconds: Optional[float] = None
    transcript_length: int = 0
    language: str = ""
    retry_count: int = 0
    success: bool = False
    error: Optional[str] = None
    
    def complete(self, success: bool = True, error: Optional[str] = None):
        """Mark transcription as complete."""
        self.completed_at = datetime.now()
        self.duration_ms = (self.completed_at - self.started_at).total_seconds() * 1000
        self.success = success
        self.error = error
    
    def to_dict(self) -> dict:
        """Convert to dictionary for logging."""
        return {
            "request_id": self.request_id,
            "duration_ms": self.duration_ms,
            "audio_size_bytes": self.audio_size_bytes,
            "audio_duration_seconds": self.audio_duration_seconds,
            "transcript_length": self.transcript_length,
            "language": self.language,
            "retry_count": self.retry_count,
            "success": self.success,
            "error": self.error,
        }


# ===================== RESPONSE TYPES =====================

@dataclass
class TranscriptionResult:
    """Result of a transcription request."""
    text: str
    language: Optional[str] = None
    duration: Optional[float] = None
    segments: list = field(default_factory=list)
    words: list = field(default_factory=list)
    
    @classmethod
    def from_api_response(cls, response: dict) -> "TranscriptionResult":
        """Create from OpenAI API response."""
        return cls(
            text=response.get("text", ""),
            language=response.get("language"),
            duration=response.get("duration"),
            segments=response.get("segments", []),
            words=response.get("words", []),
        )


# ===================== WHISPER SERVICE =====================

class WhisperService:
    """
    OpenAI Whisper Speech-to-Text service.
    
    Features:
    - Automatic retry with exponential backoff
    - Audio format validation
    - Comprehensive logging and metrics
    - Support for multiple languages (default: Vietnamese)
    """
    
    API_BASE_URL = "https://api.openai.com/v1"
    
    def __init__(self, config: Optional[WhisperConfig] = None):
        """Initialize Whisper service."""
        self.config = config or ai_config.whisper
        self._client: Optional[httpx.Client] = None
        self._request_count = 0
        
        if not self.config.validate():
            logger.warning(
                "WhisperService initialized without API key. "
                "Set OPENAI_API_KEY environment variable."
            )
    
    @property
    def client(self) -> httpx.Client:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = httpx.Client(
                base_url=self.API_BASE_URL,
                headers={
                    "Authorization": f"Bearer {self.config.api_key}",
                },
                timeout=httpx.Timeout(self.config.timeout),
            )
        return self._client
    
    def close(self):
        """Close the HTTP client."""
        if self._client:
            self._client.close()
            self._client = None
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
    
    def _generate_request_id(self) -> str:
        """Generate unique request ID."""
        self._request_count += 1
        return f"whisper_{int(time.time())}_{self._request_count}"
    
    def _should_retry(self, exception: Exception) -> bool:
        """Determine if request should be retried."""
        if isinstance(exception, httpx.HTTPStatusError):
            # Retry on rate limit (429) or server errors (5xx)
            return exception.response.status_code in (429, 500, 502, 503, 504)
        if isinstance(exception, (httpx.TimeoutException, httpx.ConnectError)):
            return True
        return False
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=2, max=30),
        retry=retry_if_exception_type((
            httpx.TimeoutException,
            httpx.ConnectError,
            AIServiceRateLimitError,
        )),
        before_sleep=before_sleep_log(logger, logging.WARNING),
    )
    def _make_request(
        self,
        audio_data: bytes,
        filename: str,
        language: Optional[str] = None,
        prompt: Optional[str] = None,
        response_format: Optional[str] = None,
    ) -> dict:
        """
        Make transcription request to Whisper API.
        
        Args:
            audio_data: Audio file bytes
            filename: Original filename
            language: Language code (e.g., 'vi' for Vietnamese)
            prompt: Optional prompt to guide transcription
            response_format: Response format (json, text, srt, etc.)
            
        Returns:
            API response dictionary
        """
        if not self.config.validate():
            raise AIServiceConfigError("OpenAI API key not configured")
        
        # Prepare form data
        files = {
            "file": (filename, io.BytesIO(audio_data)),
        }
        
        data = {
            "model": self.config.model,
        }
        
        if language:
            data["language"] = language
        elif self.config.default_language:
            data["language"] = self.config.default_language
            
        if prompt:
            data["prompt"] = prompt
            
        if response_format:
            data["response_format"] = response_format
        else:
            data["response_format"] = self.config.response_format
        
        logger.info(f"Sending transcription request: model={self.config.model}, "
                   f"language={data.get('language')}, file_size={len(audio_data)}")
        
        try:
            response = self.client.post(
                "/audio/transcriptions",
                files=files,
                data=data,
            )
            response.raise_for_status()
            return response.json()
            
        except httpx.HTTPStatusError as e:
            status_code = e.response.status_code
            
            if status_code == 429:
                logger.warning("Whisper API rate limit exceeded")
                raise AIServiceRateLimitError("Rate limit exceeded") from e
            elif status_code == 401:
                raise AIServiceConfigError("Invalid OpenAI API key") from e
            elif status_code >= 500:
                raise AIServiceError(f"Whisper API server error: {status_code}") from e
            else:
                error_body = e.response.text
                raise AIServiceError(f"Whisper API error ({status_code}): {error_body}") from e
                
        except httpx.TimeoutException as e:
            logger.warning(f"Whisper API timeout after {self.config.timeout}s")
            raise AIServiceTimeoutError(
                f"Request timed out after {self.config.timeout}s"
            ) from e
    
    def transcribe(
        self,
        audio_data: Union[bytes, BinaryIO],
        filename: str = "audio.wav",
        language: Optional[str] = None,
        prompt: Optional[str] = None,
    ) -> TranscriptionResult:
        """
        Transcribe audio to text.
        
        Args:
            audio_data: Audio file as bytes or file-like object
            filename: Original filename (used for format detection)
            language: Language code (e.g., 'vi', 'en'). Defaults to Vietnamese.
            prompt: Optional prompt to guide transcription context
            
        Returns:
            TranscriptionResult with transcribed text
            
        Raises:
            AIServiceError: On transcription failure
            AIServiceConfigError: If API key not configured
        """
        # Convert file-like to bytes if needed
        if hasattr(audio_data, 'read'):
            audio_data = audio_data.read()
        
        # Initialize metrics
        metrics = TranscriptionMetrics(
            request_id=self._generate_request_id(),
            audio_size_bytes=len(audio_data),
            language=language or self.config.default_language,
        )
        
        try:
            # Validate audio file
            audio_meta = validate_audio_file(audio_data, filename, self.config)
            
            logger.info(
                f"[{metrics.request_id}] Starting transcription: "
                f"format={audio_meta.format}, size={audio_meta.size_bytes}B"
            )
            
            # Make API request
            response = self._make_request(
                audio_data=audio_data,
                filename=filename,
                language=language,
                prompt=prompt,
            )
            
            # Parse result
            result = TranscriptionResult.from_api_response(response)
            
            # Update metrics
            metrics.transcript_length = len(result.text)
            if result.duration:
                metrics.audio_duration_seconds = result.duration
            if result.language:
                metrics.language = result.language
            metrics.complete(success=True)
            
            logger.info(
                f"[{metrics.request_id}] Transcription complete: "
                f"duration={metrics.duration_ms:.0f}ms, "
                f"text_length={metrics.transcript_length}"
            )
            
            if ai_config.log_responses:
                logger.debug(f"[{metrics.request_id}] Transcript: {result.text[:200]}...")
            
            return result
            
        except Exception as e:
            metrics.complete(success=False, error=str(e))
            logger.error(
                f"[{metrics.request_id}] Transcription failed: {e}",
                extra={"metrics": metrics.to_dict()},
            )
            raise
    
    async def transcribe_async(
        self,
        audio_data: Union[bytes, BinaryIO],
        filename: str = "audio.wav",
        language: Optional[str] = None,
        prompt: Optional[str] = None,
    ) -> TranscriptionResult:
        """
        Async version of transcribe.
        
        Note: Uses httpx.AsyncClient internally.
        """
        import asyncio
        
        # For now, run sync version in thread pool
        # TODO: Implement true async with httpx.AsyncClient
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self.transcribe,
            audio_data,
            filename,
            language,
            prompt,
        )


# ===================== SINGLETON INSTANCE =====================

_whisper_service: Optional[WhisperService] = None


def get_whisper_service() -> WhisperService:
    """Get or create global Whisper service instance."""
    global _whisper_service
    if _whisper_service is None:
        _whisper_service = WhisperService()
    return _whisper_service


def transcribe_audio(
    audio_data: Union[bytes, BinaryIO],
    filename: str = "audio.wav",
    language: Optional[str] = None,
    prompt: Optional[str] = None,
) -> TranscriptionResult:
    """
    Convenience function to transcribe audio.
    
    Args:
        audio_data: Audio file bytes or file-like object
        filename: Original filename
        language: Language code (default: Vietnamese 'vi')
        prompt: Optional context prompt
        
    Returns:
        TranscriptionResult with transcribed text
    """
    return get_whisper_service().transcribe(
        audio_data=audio_data,
        filename=filename,
        language=language,
        prompt=prompt,
    )
