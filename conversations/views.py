"""
Views for Conversation API endpoints with enhanced permissions and filtering.
"""

from django.utils import timezone
from django.db.models import Count, Avg
from rest_framework import viewsets, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly, AllowAny
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import Persona, Session, Message
from .serializers import (
    PersonaListSerializer,
    PersonaDetailSerializer,
    PersonaCreateSerializer,
    SessionListSerializer,
    SessionDetailSerializer,
    SessionCreateSerializer,
    SessionUpdateSerializer,
    SessionEndSerializer,
    MessageSerializer,
    MessageCreateSerializer,
)
from .permissions import IsOwnerOrReadOnly, IsOwner
from .filters import PersonaFilter, SessionFilter, MessageFilter


class PersonaViewSet(viewsets.ModelViewSet):
    """
    API endpoints for Persona management.
    
    Permissions:
    - List/Retrieve: Anyone (public)
    - Create: Authenticated users
    - Update/Delete: Owner or Admin only
    
    Filtering:
    - ?search=keyword - Tìm trong name, description, background
    - ?personality=friendly - Lọc theo personality type
    - ?difficulty=easy - Lọc theo difficulty level
    - ?is_active=true - Lọc theo trạng thái
    - ?ordering=-created_at - Sắp xếp
    """
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = PersonaFilter
    ordering_fields = ["name", "created_at", "difficulty_level"]
    ordering = ["-created_at"]
    
    def get_permissions(self):
        """
        Set permissions based on action:
        - list, retrieve: AllowAny (public access)
        - create: IsAuthenticated
        - update, partial_update, destroy: IsOwnerOrReadOnly
        """
        if self.action in ["list", "retrieve"]:
            permission_classes = [AllowAny]
        elif self.action == "create":
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        queryset = Persona.objects.select_related("created_by").annotate(
            total_sessions=Count("sessions")
        )
        
        # For non-authenticated users, only show active personas
        if not self.request.user.is_authenticated:
            queryset = queryset.filter(is_active=True)
        
        # For regular users, show active personas + their own
        elif not self.request.user.is_staff:
            from django.db.models import Q
            queryset = queryset.filter(
                Q(is_active=True) | Q(created_by=self.request.user)
            )
        
        return queryset
    
    def get_serializer_class(self):
        if self.action == "list":
            return PersonaListSerializer
        elif self.action in ["create", "update", "partial_update"]:
            return PersonaCreateSerializer
        return PersonaDetailSerializer
    
    @swagger_auto_schema(
        operation_description="Lấy danh sách personas với filter và search",
        responses={200: PersonaListSerializer(many=True)},
        tags=["Personas"]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_description="Xem chi tiết persona",
        responses={200: PersonaDetailSerializer()},
        tags=["Personas"]
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_description="Tạo persona mới (yêu cầu đăng nhập)",
        request_body=PersonaCreateSerializer,
        responses={201: PersonaDetailSerializer()},
        tags=["Personas"]
    )
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        persona = serializer.save()
        
        # Return full detail
        return Response(
            PersonaDetailSerializer(persona, context={"request": request}).data,
            status=status.HTTP_201_CREATED
        )
    
    @swagger_auto_schema(
        operation_description="Cập nhật persona (chỉ owner hoặc admin)",
        request_body=PersonaCreateSerializer,
        responses={200: PersonaDetailSerializer()},
        tags=["Personas"]
    )
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        persona = serializer.save()
        
        return Response(
            PersonaDetailSerializer(persona, context={"request": request}).data
        )
    
    @swagger_auto_schema(
        operation_description="Xóa persona (chỉ owner hoặc admin)",
        responses={204: "Đã xóa thành công"},
        tags=["Personas"]
    )
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        
        # Check if persona has active sessions
        active_sessions = instance.sessions.filter(status=Session.SessionStatus.ACTIVE).count()
        if active_sessions > 0:
            return Response(
                {"error": f"Không thể xóa persona đang có {active_sessions} session đang hoạt động."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        self.perform_destroy(instance)
        return Response(
            {"message": "Đã xóa persona thành công."},
            status=status.HTTP_204_NO_CONTENT
        )
    
    @swagger_auto_schema(
        operation_description="Lấy personas của user hiện tại",
        responses={200: PersonaListSerializer(many=True)},
        tags=["Personas"]
    )
    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated])
    def my_personas(self, request):
        """Get personas created by current user."""
        queryset = self.get_queryset().filter(created_by=request.user)
        serializer = PersonaListSerializer(queryset, many=True, context={"request": request})
        return Response(serializer.data)
    
    @swagger_auto_schema(
        operation_description="Lấy thống kê của persona",
        responses={
            200: openapi.Response(
                description="Thống kê persona",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "total_sessions": openapi.Schema(type=openapi.TYPE_INTEGER),
                        "completed_sessions": openapi.Schema(type=openapi.TYPE_INTEGER),
                        "average_rating": openapi.Schema(type=openapi.TYPE_NUMBER),
                        "average_duration_seconds": openapi.Schema(type=openapi.TYPE_INTEGER),
                    }
                )
            )
        },
        tags=["Personas"]
    )
    @action(detail=True, methods=["get"])
    def stats(self, request, pk=None):
        """Get statistics for a persona."""
        persona = self.get_object()
        sessions = persona.sessions.all()
        
        stats = sessions.aggregate(
            total=Count("id"),
            completed=Count("id", filter={"status": Session.SessionStatus.COMPLETED}),
            avg_rating=Avg("rating"),
            avg_duration=Avg("total_duration_seconds")
        )
        
        return Response({
            "total_sessions": stats["total"] or 0,
            "completed_sessions": stats["completed"] or 0,
            "average_rating": round(stats["avg_rating"], 2) if stats["avg_rating"] else None,
            "average_duration_seconds": int(stats["avg_duration"]) if stats["avg_duration"] else 0,
        })


class SessionViewSet(viewsets.ModelViewSet):
    """
    API endpoints for Session management.
    
    All endpoints require authentication.
    Users can only access their own sessions.
    """
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = SessionFilter
    ordering_fields = ["started_at", "rating", "total_messages"]
    ordering = ["-started_at"]
    
    def get_queryset(self):
        # Handle unauthenticated requests (e.g., during schema generation)
        if not self.request.user.is_authenticated:
            return Session.objects.none()
        
        # Only return sessions belonging to current user
        return Session.objects.filter(
            user=self.request.user
        ).select_related("persona").prefetch_related("messages")
    
    def get_serializer_class(self):
        if self.action == "list":
            return SessionListSerializer
        elif self.action == "create":
            return SessionCreateSerializer
        elif self.action in ["update", "partial_update"]:
            return SessionUpdateSerializer
        elif self.action == "end":
            return SessionEndSerializer
        elif self.action == "add_message":
            return MessageCreateSerializer
        return SessionDetailSerializer
    
    @swagger_auto_schema(
        operation_description="Lấy danh sách sessions của bạn",
        responses={200: SessionListSerializer(many=True)},
        tags=["Sessions"]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_description="Xem chi tiết session với lịch sử tin nhắn",
        responses={200: SessionDetailSerializer()},
        tags=["Sessions"]
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_description="Tạo session luyện tập mới",
        request_body=SessionCreateSerializer,
        responses={201: SessionDetailSerializer()},
        tags=["Sessions"]
    )
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        session = serializer.save()
        
        return Response(
            SessionDetailSerializer(session, context={"request": request}).data,
            status=status.HTTP_201_CREATED
        )
    
    @swagger_auto_schema(
        operation_description="Kết thúc session và đưa đánh giá",
        request_body=SessionEndSerializer,
        responses={200: SessionDetailSerializer()},
        tags=["Sessions"]
    )
    @action(detail=True, methods=["post"])
    def end(self, request, pk=None):
        """End a session and optionally provide feedback."""
        session = self.get_object()
        
        if session.status != Session.SessionStatus.ACTIVE:
            return Response(
                {"error": "Session này đã kết thúc."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = SessionEndSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Update session
        session.status = Session.SessionStatus.COMPLETED
        session.ended_at = timezone.now()
        
        if "rating" in serializer.validated_data:
            session.rating = serializer.validated_data["rating"]
        if "feedback" in serializer.validated_data:
            session.feedback = serializer.validated_data["feedback"]
        
        session.save()
        
        return Response(
            SessionDetailSerializer(session, context={"request": request}).data,
            status=status.HTTP_200_OK
        )
    
    @swagger_auto_schema(
        operation_description="Thêm tin nhắn vào session",
        request_body=MessageCreateSerializer,
        responses={201: MessageSerializer()},
        tags=["Sessions"]
    )
    @action(detail=True, methods=["post"])
    def add_message(self, request, pk=None):
        """Add a message to the session."""
        session = self.get_object()
        
        if session.status != Session.SessionStatus.ACTIVE:
            return Response(
                {"error": "Không thể thêm tin nhắn vào session đã kết thúc."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = MessageCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        message = Message.objects.create(
            session=session,
            **serializer.validated_data
        )
        
        return Response(
            MessageSerializer(message).data,
            status=status.HTTP_201_CREATED
        )
    
    @swagger_auto_schema(
        operation_description="Lấy lịch sử tin nhắn của session",
        responses={200: MessageSerializer(many=True)},
        tags=["Sessions"]
    )
    @action(detail=True, methods=["get"])
    def messages(self, request, pk=None):
        """Get all messages in a session."""
        session = self.get_object()
        messages = session.messages.all()
        return Response(MessageSerializer(messages, many=True).data)
    
    @swagger_auto_schema(
        operation_description="Bỏ qua session (không hoàn thành)",
        responses={200: SessionDetailSerializer()},
        tags=["Sessions"]
    )
    @action(detail=True, methods=["post"])
    def abandon(self, request, pk=None):
        """Abandon a session without completing it."""
        session = self.get_object()
        
        if session.status != Session.SessionStatus.ACTIVE:
            return Response(
                {"error": "Session này đã kết thúc."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        session.status = Session.SessionStatus.ABANDONED
        session.ended_at = timezone.now()
        session.save()
        
        return Response(
            SessionDetailSerializer(session, context={"request": request}).data,
            status=status.HTTP_200_OK
        )


class MessageListView(generics.ListAPIView):
    """
    API endpoint for listing messages (filtered by session).
    
    GET /api/messages/?session={session_id}
    """
    permission_classes = [IsAuthenticated]
    serializer_class = MessageSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = MessageFilter
    ordering = ["order", "created_at"]
    
    def get_queryset(self):
        # Handle unauthenticated requests
        if not self.request.user.is_authenticated:
            return Message.objects.none()
        
        session_id = self.request.query_params.get("session")
        if not session_id:
            return Message.objects.none()
        
        # Only return messages from user's own sessions
        return Message.objects.filter(
            session_id=session_id,
            session__user=self.request.user
        ).select_related("session")
    
    @swagger_auto_schema(
        operation_description="Lấy danh sách tin nhắn theo session",
        responses={200: MessageSerializer(many=True)},
        tags=["Messages"]
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
