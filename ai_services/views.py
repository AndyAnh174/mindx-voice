"""
API Views for AI Services.
"""

import logging
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from django.http import StreamingHttpResponse
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .gemini_service import gemini_service
from .whisper_service import get_whisper_service, TranscriptionResult
from .models import ChatMessage, MessageRole, PersonaContext, GenerationParams
from .exceptions import AIServiceError, AIServiceConfigError
from .serializers import (
    ChatRequestSerializer,
    ChatResponseSerializer,
    ChatStreamRequestSerializer,
)

logger = logging.getLogger(__name__)


class ChatView(APIView):
    """
    API endpoint for text-to-text chat with AI.
    
    POST /api/ai/chat/
    
    Generates a reply based on the prompt, history, and persona.
    """
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Tạo phản hồi AI từ prompt và context",
        request_body=ChatRequestSerializer,
        responses={
            200: ChatResponseSerializer(),
            400: openapi.Response(
                description="Request không hợp lệ",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "error": openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                "code": openapi.Schema(type=openapi.TYPE_STRING),
                                "message": openapi.Schema(type=openapi.TYPE_STRING),
                            }
                        )
                    }
                )
            ),
            500: openapi.Response(description="Lỗi AI service"),
        },
        tags=["AI"]
    )
    def post(self, request):
        """Generate AI response."""
        serializer = ChatRequestSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                {"error": {"code": "INVALID_REQUEST", "message": "Dữ liệu không hợp lệ", "details": serializer.errors}},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        data = serializer.validated_data
        
        try:
            # Build history
            history = []
            for msg in data.get("history", []):
                history.append(ChatMessage(
                    role=MessageRole(msg["role"]),
                    content=msg["content"]
                ))
            
            # Build persona context
            persona = None
            if data.get("persona"):
                persona_data = data["persona"]
                persona = PersonaContext(
                    name=persona_data.get("name", "Phụ huynh"),
                    personality_type=persona_data.get("personality_type", "friendly"),
                    description=persona_data.get("description", ""),
                    background=persona_data.get("background", ""),
                    communication_style=persona_data.get("communication_style", ""),
                    common_concerns=persona_data.get("common_concerns", ""),
                    child_name=persona_data.get("child_name", ""),
                    child_age=persona_data.get("child_age"),
                    child_grade=persona_data.get("child_grade", ""),
                    system_prompt=persona_data.get("system_prompt", ""),
                )
            
            # Build params
            params_data = data.get("params", {})
            params = GenerationParams(
                max_tokens=params_data.get("max_tokens", 2048),
                temperature=params_data.get("temperature", 0.7),
                top_p=params_data.get("top_p", 0.95),
                top_k=params_data.get("top_k", 40),
            )
            
            # Generate reply
            response = gemini_service.generate_reply(
                prompt=data["prompt"],
                history=history,
                persona=persona,
                params=params,
            )
            
            return Response({
                "success": True,
                "data": response.to_dict()
            })
            
        except AIServiceError as e:
            logger.error(f"AI service error: {e.code} - {e.message}")
            return Response(
                e.to_dict(),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        except Exception as e:
            logger.exception(f"Unexpected error in chat: {e}")
            return Response(
                {"error": {"code": "INTERNAL_ERROR", "message": "Lỗi hệ thống. Vui lòng thử lại."}},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ChatStreamView(APIView):
    """
    API endpoint for streaming text-to-text chat with AI.
    
    POST /api/ai/chat/stream/
    
    Returns a streaming response with Server-Sent Events (SSE).
    """
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Tạo phản hồi AI với streaming (SSE)",
        request_body=ChatStreamRequestSerializer,
        responses={
            200: openapi.Response(
                description="Stream response (text/event-stream)",
            ),
        },
        tags=["AI"]
    )
    def post(self, request):
        """Generate streaming AI response."""
        serializer = ChatStreamRequestSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                {"error": {"code": "INVALID_REQUEST", "message": "Dữ liệu không hợp lệ", "details": serializer.errors}},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        data = serializer.validated_data
        
        def event_stream():
            try:
                # Build history
                history = []
                for msg in data.get("history", []):
                    history.append(ChatMessage(
                        role=MessageRole(msg["role"]),
                        content=msg["content"]
                    ))
                
                # Build persona context
                persona = None
                if data.get("persona"):
                    persona_data = data["persona"]
                    persona = PersonaContext(
                        name=persona_data.get("name", "Phụ huynh"),
                        personality_type=persona_data.get("personality_type", "friendly"),
                        description=persona_data.get("description", ""),
                        system_prompt=persona_data.get("system_prompt", ""),
                    )
                
                # Build params
                params_data = data.get("params", {})
                params = GenerationParams(
                    max_tokens=params_data.get("max_tokens", 2048),
                    temperature=params_data.get("temperature", 0.7),
                )
                
                # Stream response
                import json
                for chunk in gemini_service.generate_reply_stream(
                    prompt=data["prompt"],
                    history=history,
                    persona=persona,
                    params=params,
                ):
                    yield f"data: {json.dumps(chunk.to_dict())}\n\n"
                
                yield "data: [DONE]\n\n"
                
            except AIServiceError as e:
                import json
                yield f"data: {json.dumps(e.to_dict())}\n\n"
            except Exception as e:
                import json
                yield f"data: {json.dumps({'error': {'code': 'STREAM_ERROR', 'message': str(e)}})}\n\n"
        
        response = StreamingHttpResponse(
            event_stream(),
            content_type="text/event-stream"
        )
        response["Cache-Control"] = "no-cache"
        response["X-Accel-Buffering"] = "no"
        return response


class TranscribeAudioView(APIView):
    """
    API endpoint for Speech-to-Text transcription using Whisper.
    
    POST /api/ai/transcribe/
    
    Transcribes audio file to text.
    """
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    
    @swagger_auto_schema(
        operation_description="Chuyển đổi giọng nói thành văn bản (Speech-to-Text)",
        manual_parameters=[
            openapi.Parameter(
                "audio",
                openapi.IN_FORM,
                type=openapi.TYPE_FILE,
                required=True,
                description="File audio (mp3, wav, webm, ogg, m4a, flac)"
            ),
            openapi.Parameter(
                "language",
                openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                required=False,
                description="Mã ngôn ngữ (vi, en, etc.). Mặc định: vi"
            ),
            openapi.Parameter(
                "prompt",
                openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                required=False,
                description="Context prompt để hỗ trợ nhận dạng"
            ),
        ],
        responses={
            200: openapi.Response(
                description="Transcription result",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "success": openapi.Schema(type=openapi.TYPE_BOOLEAN),
                        "text": openapi.Schema(type=openapi.TYPE_STRING),
                        "language": openapi.Schema(type=openapi.TYPE_STRING),
                        "duration": openapi.Schema(type=openapi.TYPE_NUMBER),
                    }
                )
            ),
            400: openapi.Response(description="Invalid audio file"),
            500: openapi.Response(description="Transcription error"),
        },
        tags=["AI"]
    )
    def post(self, request):
        """Transcribe audio to text."""
        # Get audio file
        audio_file = request.FILES.get("audio")
        if not audio_file:
            return Response(
                {"error": {"code": "MISSING_AUDIO", "message": "Vui lòng upload file audio"}},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        language = request.data.get("language", "vi")
        prompt = request.data.get("prompt", "")
        
        try:
            whisper = get_whisper_service()
            
            # Read file data
            audio_data = audio_file.read()
            filename = audio_file.name or "audio.wav"
            
            logger.info(f"Transcribing audio: {filename}, size={len(audio_data)}, language={language}")
            
            # Transcribe
            result = whisper.transcribe(
                audio_data=audio_data,
                filename=filename,
                language=language,
                prompt=prompt if prompt else None,
            )
            
            return Response({
                "success": True,
                "text": result.text,
                "language": result.language,
                "duration": result.duration,
            })
            
        except AIServiceConfigError as e:
            logger.warning(f"Whisper not configured: {e}")
            return Response(
                {"error": {"code": "NOT_CONFIGURED", "message": "Whisper API chưa được cấu hình"}},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        except AIServiceError as e:
            logger.error(f"Transcription error: {e.code} - {e.message}")
            return Response(
                e.to_dict(),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        except Exception as e:
            logger.exception(f"Unexpected error in transcription: {e}")
            return Response(
                {"error": {"code": "INTERNAL_ERROR", "message": "Lỗi chuyển đổi giọng nói. Vui lòng thử lại."}},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AIHealthView(APIView):
    """
    Health check endpoint for AI services.
    """
    permission_classes = []
    
    @swagger_auto_schema(
        operation_description="Kiểm tra trạng thái AI service",
        responses={
            200: openapi.Response(
                description="AI service status",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "status": openapi.Schema(type=openapi.TYPE_STRING),
                        "services": openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                "gemini": openapi.Schema(type=openapi.TYPE_OBJECT),
                                "whisper": openapi.Schema(type=openapi.TYPE_OBJECT),
                            }
                        ),
                    }
                )
            )
        },
        tags=["AI"]
    )
    def get(self, request):
        """Check AI service health."""
        from .config import ai_config
        
        return Response({
            "status": "ok",
            "services": {
                "gemini": {
                    "status": "ok" if ai_config.gemini.validate() else "not_configured",
                    "model": ai_config.gemini.model,
                    "configured": ai_config.gemini.validate(),
                },
                "whisper": {
                    "status": "ok" if ai_config.whisper.validate() else "not_configured",
                    "model": ai_config.whisper.model,
                    "configured": ai_config.whisper.validate(),
                    "supported_formats": ai_config.whisper.supported_formats,
                    "max_file_size_mb": ai_config.whisper.max_file_size_mb,
                },
            },
            "default_provider": ai_config.default_provider,
        })

