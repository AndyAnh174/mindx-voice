"""
API Views for AI Services.
"""

import logging
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.http import StreamingHttpResponse
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .gemini_service import gemini_service
from .models import ChatMessage, MessageRole, PersonaContext, GenerationParams
from .exceptions import AIServiceError
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
                        "provider": openapi.Schema(type=openapi.TYPE_STRING),
                        "model": openapi.Schema(type=openapi.TYPE_STRING),
                        "configured": openapi.Schema(type=openapi.TYPE_BOOLEAN),
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
            "status": "ok" if ai_config.gemini.validate() else "not_configured",
            "provider": ai_config.default_provider,
            "model": ai_config.gemini.model,
            "configured": ai_config.gemini.validate(),
        })
