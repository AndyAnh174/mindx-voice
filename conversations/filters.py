"""
Filters for Conversations API.
"""

from django_filters import rest_framework as filters
from .models import Persona, Session, Message


class PersonaFilter(filters.FilterSet):
    """
    Filter for Persona model.
    
    Usage:
    - ?search=keyword - Tìm trong name, description, background
    - ?name=keyword - Tìm theo tên (contains, case-insensitive)
    - ?personality=friendly - Lọc theo personality type
    - ?difficulty=easy - Lọc theo difficulty level
    - ?is_active=true - Lọc theo trạng thái
    - ?created_by=user_id - Lọc theo người tạo
    """
    
    # Search across multiple fields
    search = filters.CharFilter(method="search_filter", label="Tìm kiếm")
    
    # Individual field filters
    name = filters.CharFilter(lookup_expr="icontains", label="Tên")
    description = filters.CharFilter(lookup_expr="icontains", label="Mô tả")
    personality = filters.ChoiceFilter(
        field_name="personality_type",
        choices=Persona.PersonalityType.choices,
        label="Kiểu tính cách"
    )
    difficulty = filters.ChoiceFilter(
        field_name="difficulty_level",
        choices=Persona.DifficultyLevel.choices,
        label="Mức độ khó"
    )
    is_active = filters.BooleanFilter(label="Đang hoạt động")
    created_by = filters.UUIDFilter(field_name="created_by__id", label="Người tạo")
    
    # Date range filters
    created_after = filters.DateTimeFilter(
        field_name="created_at",
        lookup_expr="gte",
        label="Tạo sau"
    )
    created_before = filters.DateTimeFilter(
        field_name="created_at",
        lookup_expr="lte",
        label="Tạo trước"
    )
    
    class Meta:
        model = Persona
        fields = [
            "search", "name", "description", "personality", 
            "difficulty", "is_active", "created_by",
            "created_after", "created_before"
        ]
    
    def search_filter(self, queryset, name, value):
        """
        Search across name, description, and background fields.
        """
        from django.db.models import Q
        
        if not value:
            return queryset
        
        return queryset.filter(
            Q(name__icontains=value) |
            Q(description__icontains=value) |
            Q(background__icontains=value) |
            Q(child_name__icontains=value)
        )


class SessionFilter(filters.FilterSet):
    """
    Filter for Session model.
    
    Usage:
    - ?status=active - Lọc theo trạng thái
    - ?persona=uuid - Lọc theo persona
    - ?rating_min=3 - Đánh giá tối thiểu
    - ?has_feedback=true - Có feedback hay không
    """
    
    status = filters.ChoiceFilter(
        choices=Session.SessionStatus.choices,
        label="Trạng thái"
    )
    persona = filters.UUIDFilter(field_name="persona__id", label="Persona")
    persona_name = filters.CharFilter(
        field_name="persona__name",
        lookup_expr="icontains",
        label="Tên persona"
    )
    
    # Rating filters
    rating_min = filters.NumberFilter(
        field_name="rating",
        lookup_expr="gte",
        label="Đánh giá tối thiểu"
    )
    rating_max = filters.NumberFilter(
        field_name="rating",
        lookup_expr="lte",
        label="Đánh giá tối đa"
    )
    has_feedback = filters.BooleanFilter(
        method="filter_has_feedback",
        label="Có feedback"
    )
    
    # Date range
    started_after = filters.DateTimeFilter(
        field_name="started_at",
        lookup_expr="gte",
        label="Bắt đầu sau"
    )
    started_before = filters.DateTimeFilter(
        field_name="started_at",
        lookup_expr="lte",
        label="Bắt đầu trước"
    )
    
    class Meta:
        model = Session
        fields = [
            "status", "persona", "persona_name",
            "rating_min", "rating_max", "has_feedback",
            "started_after", "started_before"
        ]
    
    def filter_has_feedback(self, queryset, name, value):
        """Filter sessions that have/don't have feedback."""
        if value:
            return queryset.exclude(feedback="")
        return queryset.filter(feedback="")


class MessageFilter(filters.FilterSet):
    """
    Filter for Message model.
    """
    
    session = filters.UUIDFilter(field_name="session__id", label="Session")
    role = filters.ChoiceFilter(
        choices=Message.MessageRole.choices,
        label="Vai trò"
    )
    message_type = filters.ChoiceFilter(
        choices=Message.MessageType.choices,
        label="Loại tin nhắn"
    )
    
    class Meta:
        model = Message
        fields = ["session", "role", "message_type"]
