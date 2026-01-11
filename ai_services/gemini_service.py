"""
Gemini AI Service Implementation.

Provides the main interface for interacting with Google's Gemini API.
"""

import logging
import time
from typing import Optional, Generator, List

import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from google.api_core import exceptions as google_exceptions
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from .config import GeminiConfig, ai_config
from .exceptions import (
    AIServiceError,
    APIKeyError,
    RateLimitError,
    QuotaExceededError,
    ModelError,
    ContentFilterError,
    TimeoutError,
    NetworkError,
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


logger = logging.getLogger(__name__)


class GeminiService:
    """
    Service for interacting with Google Gemini API.
    
    Features:
    - Text generation with conversation history
    - Persona-based chat
    - Streaming support
    - Retry with exponential backoff
    - Comprehensive error handling
    """
    
    def __init__(self, config: Optional[GeminiConfig] = None):
        """Initialize the Gemini service."""
        self.config = config or ai_config.gemini
        self._model = None
        self._initialized = False
        
    def _initialize(self) -> None:
        """Initialize the Gemini client."""
        if self._initialized:
            return
        
        if not self.config.validate():
            raise APIKeyError("GEMINI_API_KEY chưa được cấu hình trong environment variables.")
        
        try:
            genai.configure(api_key=self.config.api_key)
            
            # Configure safety settings
            safety_settings = None
            if not self.config.block_dangerous_content:
                safety_settings = {
                    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
                }
            
            self._model = genai.GenerativeModel(
                model_name=self.config.model,
                safety_settings=safety_settings,
            )
            self._initialized = True
            
            logger.info(f"Gemini service initialized with model: {self.config.model}")
            
        except Exception as e:
            logger.error(f"Failed to initialize Gemini service: {e}")
            raise ModelError(f"Không thể khởi tạo Gemini: {str(e)}")
    
    def _build_chat_history(self, messages: List[ChatMessage]) -> List[dict]:
        """Convert messages to Gemini format."""
        history = []
        
        for msg in messages:
            if msg.role == MessageRole.SYSTEM:
                # Gemini doesn't have system role, prepend to first user message
                continue
            history.append(msg.to_gemini_format())
        
        return history
    
    def _get_system_instruction(self, messages: List[ChatMessage]) -> Optional[str]:
        """Extract system instruction from messages."""
        for msg in messages:
            if msg.role == MessageRole.SYSTEM:
                return msg.content
        return None
    
    def _handle_error(self, error: Exception) -> None:
        """Convert Google API errors to our custom exceptions."""
        error_str = str(error).lower()
        
        if isinstance(error, google_exceptions.InvalidArgument):
            if "api key" in error_str or "api_key" in error_str:
                raise APIKeyError()
            raise GenerationError(f"Request không hợp lệ: {error}")
        
        elif isinstance(error, google_exceptions.PermissionDenied):
            raise APIKeyError("API key không có quyền truy cập.")
        
        elif isinstance(error, google_exceptions.ResourceExhausted):
            if "quota" in error_str:
                raise QuotaExceededError()
            raise RateLimitError()
        
        elif isinstance(error, google_exceptions.DeadlineExceeded):
            raise TimeoutError()
        
        elif isinstance(error, google_exceptions.ServiceUnavailable):
            raise NetworkError("Dịch vụ Gemini tạm thời không khả dụng.")
        
        elif isinstance(error, google_exceptions.InternalServerError):
            raise GenerationError("Lỗi server Gemini. Vui lòng thử lại.")
        
        elif "blocked" in error_str or "safety" in error_str:
            raise ContentFilterError()
        
        else:
            raise GenerationError(f"Lỗi không xác định: {error}")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((
            google_exceptions.ServiceUnavailable,
            google_exceptions.DeadlineExceeded,
            google_exceptions.InternalServerError,
        )),
        before_sleep=lambda retry_state: logger.warning(
            f"Retrying Gemini request, attempt {retry_state.attempt_number}"
        ),
    )
    def generate_reply(
        self,
        prompt: str,
        history: Optional[List[ChatMessage]] = None,
        persona: Optional[PersonaContext] = None,
        params: Optional[GenerationParams] = None,
    ) -> GenerationResponse:
        """
        Generate a reply using Gemini.
        
        Args:
            prompt: The user's input message
            history: Previous conversation messages
            persona: Persona context for roleplay
            params: Generation parameters
            
        Returns:
            GenerationResponse with the generated content
            
        Raises:
            AIServiceError: Various errors that can occur
        """
        self._initialize()
        
        # Build request
        request = GenerationRequest(
            prompt=prompt,
            history=history or [],
            persona=persona,
            params=params or GenerationParams(),
        )
        
        start_time = time.time()
        
        try:
            # Get full message history
            full_history = request.get_full_history()
            system_instruction = self._get_system_instruction(full_history)
            
            # Create model with system instruction if provided
            model = self._model
            if system_instruction:
                model = genai.GenerativeModel(
                    model_name=self.config.model,
                    system_instruction=system_instruction,
                )
            
            # Build chat history (excluding system and last user message)
            chat_history = self._build_chat_history(full_history[:-1])
            
            # Create chat and send message
            chat = model.start_chat(history=chat_history)
            
            response = chat.send_message(
                prompt,
                generation_config=request.params.to_gemini_config(),
            )
            
            # Calculate latency
            latency_ms = (time.time() - start_time) * 1000
            
            # Extract response
            content = response.text
            tokens_used = 0
            
            # Try to get token count
            if hasattr(response, "usage_metadata"):
                tokens_used = getattr(response.usage_metadata, "total_token_count", 0)
            
            # Determine finish reason
            finish_reason = "stop"
            if hasattr(response, "prompt_feedback"):
                if response.prompt_feedback.block_reason:
                    finish_reason = "content_filter"
            
            logger.info(
                f"Gemini generation completed: "
                f"tokens={tokens_used}, latency={latency_ms:.0f}ms"
            )
            
            return GenerationResponse(
                content=content,
                finish_reason=finish_reason,
                tokens_used=tokens_used,
                model=self.config.model,
                latency_ms=latency_ms,
            )
            
        except AIServiceError:
            raise
        except Exception as e:
            logger.error(f"Gemini generation error: {e}")
            self._handle_error(e)
    
    def generate_reply_stream(
        self,
        prompt: str,
        history: Optional[List[ChatMessage]] = None,
        persona: Optional[PersonaContext] = None,
        params: Optional[GenerationParams] = None,
    ) -> Generator[StreamChunk, None, None]:
        """
        Generate a reply using Gemini with streaming.
        
        Args:
            prompt: The user's input message
            history: Previous conversation messages
            persona: Persona context for roleplay
            params: Generation parameters
            
        Yields:
            StreamChunk objects with partial content
            
        Raises:
            AIServiceError: Various errors that can occur
        """
        self._initialize()
        
        # Build request
        request = GenerationRequest(
            prompt=prompt,
            history=history or [],
            persona=persona,
            params=params or GenerationParams(),
            stream=True,
        )
        
        try:
            # Get full message history
            full_history = request.get_full_history()
            system_instruction = self._get_system_instruction(full_history)
            
            # Create model with system instruction if provided
            model = self._model
            if system_instruction:
                model = genai.GenerativeModel(
                    model_name=self.config.model,
                    system_instruction=system_instruction,
                )
            
            # Build chat history
            chat_history = self._build_chat_history(full_history[:-1])
            
            # Create chat and stream response
            chat = model.start_chat(history=chat_history)
            
            response = chat.send_message(
                prompt,
                generation_config=request.params.to_gemini_config(),
                stream=True,
            )
            
            total_tokens = 0
            
            for chunk in response:
                if chunk.text:
                    yield StreamChunk(
                        content=chunk.text,
                        is_final=False,
                        tokens_used=0,
                    )
            
            # Try to get final token count
            if hasattr(response, "usage_metadata"):
                total_tokens = getattr(response.usage_metadata, "total_token_count", 0)
            
            # Final chunk
            yield StreamChunk(
                content="",
                is_final=True,
                tokens_used=total_tokens,
            )
            
            logger.info(f"Gemini streaming completed: tokens={total_tokens}")
            
        except AIServiceError:
            raise
        except Exception as e:
            logger.error(f"Gemini streaming error: {e}")
            self._handle_error(e)
    
    async def generate_reply_async(
        self,
        prompt: str,
        history: Optional[List[ChatMessage]] = None,
        persona: Optional[PersonaContext] = None,
        params: Optional[GenerationParams] = None,
    ) -> GenerationResponse:
        """
        Async version of generate_reply.
        
        Note: Uses sync API in thread pool as Gemini SDK doesn't have native async.
        """
        import asyncio
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self.generate_reply(prompt, history, persona, params)
        )


# Global service instance
gemini_service = GeminiService()


def generate_reply(
    prompt: str,
    history: Optional[List[ChatMessage]] = None,
    persona: Optional[PersonaContext] = None,
    params: Optional[GenerationParams] = None,
) -> GenerationResponse:
    """
    Convenience function for generating replies.
    
    This is the main interface for the AI service.
    """
    return gemini_service.generate_reply(prompt, history, persona, params)


def generate_reply_stream(
    prompt: str,
    history: Optional[List[ChatMessage]] = None,
    persona: Optional[PersonaContext] = None,
    params: Optional[GenerationParams] = None,
) -> Generator[StreamChunk, None, None]:
    """
    Convenience function for streaming replies.
    """
    return gemini_service.generate_reply_stream(prompt, history, persona, params)
