"""
Serializers for AI Services API.
"""

from rest_framework import serializers


class ChatMessageSerializer(serializers.Serializer):
    """Serializer for a chat message in AI context."""
    
    role = serializers.ChoiceField(
        choices=["user", "assistant", "system"],
        help_text="Vai trò của người gửi"
    )
    content = serializers.CharField(
        help_text="Nội dung tin nhắn"
    )


class PersonaContextSerializer(serializers.Serializer):
    """Serializer for persona context."""
    
    name = serializers.CharField(
        required=False,
        default="Phụ huynh",
        allow_blank=True,
        help_text="Tên persona"
    )
    personality_type = serializers.CharField(
        required=False,
        default="friendly",
        allow_blank=True,
        help_text="Kiểu tính cách"
    )
    description = serializers.CharField(
        required=False,
        default="",
        allow_blank=True,
        help_text="Mô tả"
    )
    background = serializers.CharField(
        required=False,
        default="",
        allow_blank=True,
        help_text="Hoàn cảnh"
    )
    communication_style = serializers.CharField(
        required=False,
        default="",
        allow_blank=True,
        help_text="Phong cách giao tiếp"
    )
    common_concerns = serializers.CharField(
        required=False,
        default="",
        allow_blank=True,
        help_text="Mối quan tâm"
    )
    child_name = serializers.CharField(
        required=False,
        default="",
        allow_blank=True,
        help_text="Tên con"
    )
    child_age = serializers.IntegerField(
        required=False,
        allow_null=True,
        help_text="Tuổi con"
    )
    child_grade = serializers.CharField(
        required=False,
        default="",
        allow_blank=True,
        help_text="Lớp con"
    )
    system_prompt = serializers.CharField(
        required=False,
        default="",
        allow_blank=True,
        help_text="System prompt tùy chỉnh"
    )


class GenerationParamsSerializer(serializers.Serializer):
    """Serializer for generation parameters."""
    
    max_tokens = serializers.IntegerField(
        required=False,
        default=2048,
        min_value=1,
        max_value=8192,
        help_text="Số token tối đa"
    )
    temperature = serializers.FloatField(
        required=False,
        default=0.7,
        min_value=0.0,
        max_value=2.0,
        help_text="Temperature (0-2)"
    )
    top_p = serializers.FloatField(
        required=False,
        default=0.95,
        min_value=0.0,
        max_value=1.0,
        help_text="Top-p sampling"
    )
    top_k = serializers.IntegerField(
        required=False,
        default=40,
        min_value=1,
        max_value=100,
        help_text="Top-k sampling"
    )


class ChatRequestSerializer(serializers.Serializer):
    """Serializer for chat request."""
    
    prompt = serializers.CharField(
        required=True,
        help_text="Nội dung tin nhắn của người dùng"
    )
    history = ChatMessageSerializer(
        many=True,
        required=False,
        default=[],
        help_text="Lịch sử hội thoại"
    )
    persona = PersonaContextSerializer(
        required=False,
        allow_null=True,
        help_text="Thông tin persona"
    )
    params = GenerationParamsSerializer(
        required=False,
        help_text="Tham số generation"
    )
    
    def validate_prompt(self, value):
        """Validate prompt is not empty."""
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Prompt không được để trống.")
        if len(value) > 10000:
            raise serializers.ValidationError("Prompt không được quá 10000 ký tự.")
        return value


class ChatStreamRequestSerializer(ChatRequestSerializer):
    """Serializer for streaming chat request."""
    pass


class ChatResponseSerializer(serializers.Serializer):
    """Serializer for chat response."""
    
    success = serializers.BooleanField()
    data = serializers.DictField(
        child=serializers.CharField(),
        help_text="Response data"
    )


class StreamChunkSerializer(serializers.Serializer):
    """Serializer for streaming chunk."""
    
    content = serializers.CharField()
    is_final = serializers.BooleanField()
    tokens_used = serializers.IntegerField()
