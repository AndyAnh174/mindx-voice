"""
Serializers for Conversation models with enhanced validation.
"""

import re
from rest_framework import serializers
from .models import Persona, Session, Message


class PersonaListSerializer(serializers.ModelSerializer):
    """
    Serializer for listing Personas (minimal info).
    """
    personality_type_display = serializers.CharField(
        source="get_personality_type_display", 
        read_only=True
    )
    difficulty_level_display = serializers.CharField(
        source="get_difficulty_level_display", 
        read_only=True
    )
    session_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Persona
        fields = [
            "id", "name", "avatar", "description",
            "personality_type", "personality_type_display",
            "difficulty_level", "difficulty_level_display",
            "is_active", "session_count", "created_at"
        ]
    
    def get_session_count(self, obj):
        """Get total number of sessions using this persona."""
        return obj.sessions.count()


class PersonaDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for Persona detail view.
    """
    personality_type_display = serializers.CharField(
        source="get_personality_type_display", 
        read_only=True
    )
    difficulty_level_display = serializers.CharField(
        source="get_difficulty_level_display", 
        read_only=True
    )
    created_by_email = serializers.EmailField(
        source="created_by.email", 
        read_only=True
    )
    session_count = serializers.SerializerMethodField()
    is_owner = serializers.SerializerMethodField()
    
    class Meta:
        model = Persona
        fields = [
            "id", "name", "avatar", "description",
            "personality_type", "personality_type_display",
            "difficulty_level", "difficulty_level_display",
            "background", "child_name", "child_age", "child_grade",
            "communication_style", "common_concerns", "system_prompt",
            "is_active", "created_by", "created_by_email",
            "session_count", "is_owner",
            "created_at", "updated_at"
        ]
        read_only_fields = ["id", "created_by", "created_at", "updated_at"]
    
    def get_session_count(self, obj):
        return obj.sessions.count()
    
    def get_is_owner(self, obj):
        """Check if current user is the owner."""
        request = self.context.get("request")
        if request and hasattr(request, "user"):
            return obj.created_by == request.user
        return False


class PersonaCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating/updating Personas with validation.
    """
    
    class Meta:
        model = Persona
        fields = [
            "name", "avatar", "description",
            "personality_type", "difficulty_level",
            "background", "child_name", "child_age", "child_grade",
            "communication_style", "common_concerns", "system_prompt",
            "is_active"
        ]
    
    def validate_name(self, value):
        """Validate persona name."""
        value = value.strip()
        
        if len(value) < 2:
            raise serializers.ValidationError(
                "Tên persona phải có ít nhất 2 ký tự."
            )
        
        if len(value) > 100:
            raise serializers.ValidationError(
                "Tên persona không được quá 100 ký tự."
            )
        
        # Check for duplicate name (case-insensitive)
        existing = Persona.objects.filter(name__iexact=value)
        if self.instance:
            existing = existing.exclude(pk=self.instance.pk)
        
        if existing.exists():
            raise serializers.ValidationError(
                "Đã tồn tại persona với tên này."
            )
        
        return value
    
    def validate_description(self, value):
        """Validate description."""
        value = value.strip()
        
        if len(value) < 10:
            raise serializers.ValidationError(
                "Mô tả phải có ít nhất 10 ký tự."
            )
        
        if len(value) > 1000:
            raise serializers.ValidationError(
                "Mô tả không được quá 1000 ký tự."
            )
        
        return value
    
    def validate_system_prompt(self, value):
        """Validate system prompt."""
        value = value.strip()
        
        if len(value) < 50:
            raise serializers.ValidationError(
                "System prompt phải có ít nhất 50 ký tự để đảm bảo AI có đủ context."
            )
        
        if len(value) > 4000:
            raise serializers.ValidationError(
                "System prompt không được quá 4000 ký tự."
            )
        
        return value
    
    def validate_child_age(self, value):
        """Validate child age."""
        if value is not None:
            if value < 1 or value > 25:
                raise serializers.ValidationError(
                    "Tuổi con phải từ 1 đến 25."
                )
        return value
    
    def validate(self, attrs):
        """Cross-field validation."""
        # If child_name is provided, child_age should also be provided
        child_name = attrs.get("child_name", "")
        child_age = attrs.get("child_age")
        
        if child_name and not child_age:
            raise serializers.ValidationError({
                "child_age": "Vui lòng cung cấp tuổi của con."
            })
        
        return attrs
    
    def create(self, validated_data):
        # Set created_by to current user
        validated_data["created_by"] = self.context["request"].user
        return super().create(validated_data)


class MessageSerializer(serializers.ModelSerializer):
    """
    Serializer for Message model.
    """
    role_display = serializers.CharField(
        source="get_role_display", 
        read_only=True
    )
    message_type_display = serializers.CharField(
        source="get_message_type_display", 
        read_only=True
    )
    
    class Meta:
        model = Message
        fields = [
            "id", "role", "role_display", "content",
            "message_type", "message_type_display",
            "audio_url", "audio_duration_seconds",
            "tokens_used", "order", "created_at"
        ]
        read_only_fields = ["id", "order", "tokens_used", "created_at"]


class MessageCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating messages with validation.
    """
    class Meta:
        model = Message
        fields = ["role", "content", "message_type", "audio_url", "audio_duration_seconds"]
    
    def validate_role(self, value):
        # Only allow user messages to be created via API
        if value not in [Message.MessageRole.USER, Message.MessageRole.ASSISTANT]:
            raise serializers.ValidationError(
                "Chỉ có thể tạo tin nhắn với vai trò 'user' hoặc 'assistant'."
            )
        return value
    
    def validate_content(self, value):
        """Validate message content."""
        value = value.strip()
        
        if not value:
            raise serializers.ValidationError(
                "Nội dung tin nhắn không được để trống."
            )
        
        if len(value) > 10000:
            raise serializers.ValidationError(
                "Nội dung tin nhắn không được quá 10000 ký tự."
            )
        
        return value
    
    def validate(self, attrs):
        """Cross-field validation."""
        message_type = attrs.get("message_type", Message.MessageType.TEXT)
        audio_url = attrs.get("audio_url", "")
        
        # If message type is voice, audio_url should be provided
        if message_type == Message.MessageType.VOICE and not audio_url:
            raise serializers.ValidationError({
                "audio_url": "Tin nhắn voice cần có URL audio."
            })
        
        return attrs


class SessionListSerializer(serializers.ModelSerializer):
    """
    Serializer for listing Sessions.
    """
    persona_name = serializers.CharField(source="persona.name", read_only=True)
    persona_avatar = serializers.ImageField(source="persona.avatar", read_only=True)
    status_display = serializers.CharField(
        source="get_status_display", 
        read_only=True
    )
    duration_formatted = serializers.SerializerMethodField()
    
    class Meta:
        model = Session
        fields = [
            "id", "persona", "persona_name", "persona_avatar",
            "title", "status", "status_display",
            "total_messages", "total_duration_seconds", "duration_formatted",
            "rating", "score", "started_at", "ended_at"
        ]
    
    def get_duration_formatted(self, obj):
        """Format duration as HH:MM:SS or MM:SS."""
        seconds = obj.total_duration_seconds
        if seconds < 3600:
            minutes = seconds // 60
            secs = seconds % 60
            return f"{minutes:02d}:{secs:02d}"
        else:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            secs = seconds % 60
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"


class SessionDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for Session detail with messages.
    """
    persona = PersonaListSerializer(read_only=True)
    messages = MessageSerializer(many=True, read_only=True)
    status_display = serializers.CharField(
        source="get_status_display", 
        read_only=True
    )
    user_email = serializers.EmailField(source="user.email", read_only=True)
    duration_formatted = serializers.SerializerMethodField()
    
    class Meta:
        model = Session
        fields = [
            "id", "user", "user_email", "persona",
            "title", "scenario", "status", "status_display",
            "total_messages", "total_duration_seconds", "duration_formatted",
            "rating", "feedback", "ai_feedback", "score",
            "started_at", "ended_at", "messages"
        ]
        read_only_fields = [
            "id", "user", "total_messages", "total_duration_seconds",
            "started_at", "ended_at"
        ]
    
    def get_duration_formatted(self, obj):
        seconds = obj.total_duration_seconds
        if seconds < 3600:
            minutes = seconds // 60
            secs = seconds % 60
            return f"{minutes:02d}:{secs:02d}"
        else:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            secs = seconds % 60
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"


class SessionCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating a new Session.
    """
    class Meta:
        model = Session
        fields = ["persona", "title", "scenario"]
    
    def validate_persona(self, value):
        if not value.is_active:
            raise serializers.ValidationError("Persona này không khả dụng.")
        return value
    
    def validate_title(self, value):
        """Validate title if provided."""
        if value:
            value = value.strip()
            if len(value) > 255:
                raise serializers.ValidationError(
                    "Tiêu đề không được quá 255 ký tự."
                )
        return value
    
    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)


class SessionUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating Session (status, feedback).
    """
    class Meta:
        model = Session
        fields = ["status", "rating", "feedback"]
    
    def validate_rating(self, value):
        if value and (value < 1 or value > 5):
            raise serializers.ValidationError("Đánh giá phải từ 1 đến 5 sao.")
        return value
    
    def validate_feedback(self, value):
        """Validate feedback."""
        if value:
            value = value.strip()
            if len(value) > 2000:
                raise serializers.ValidationError(
                    "Phản hồi không được quá 2000 ký tự."
                )
        return value


class SessionEndSerializer(serializers.Serializer):
    """
    Serializer for ending a session.
    """
    rating = serializers.IntegerField(min_value=1, max_value=5, required=False)
    feedback = serializers.CharField(required=False, allow_blank=True, max_length=2000)
