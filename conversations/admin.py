"""
Admin configuration for Conversation models.
"""

from django.contrib import admin
from .models import Persona, Session, Message


@admin.register(Persona)
class PersonaAdmin(admin.ModelAdmin):
    """Admin configuration for Persona model."""
    
    list_display = [
        "name", "personality_type", "difficulty_level", 
        "is_active", "created_at"
    ]
    list_filter = ["personality_type", "difficulty_level", "is_active", "created_at"]
    search_fields = ["name", "description", "background", "child_name"]
    ordering = ["-created_at"]
    readonly_fields = ["id", "created_at", "updated_at"]
    
    fieldsets = (
        ("Thông tin cơ bản", {
            "fields": ("id", "name", "avatar", "description")
        }),
        ("Đặc điểm Persona", {
            "fields": ("personality_type", "difficulty_level", "background")
        }),
        ("Thông tin con", {
            "fields": ("child_name", "child_age", "child_grade"),
            "classes": ("collapse",)
        }),
        ("Phong cách giao tiếp", {
            "fields": ("communication_style", "common_concerns", "system_prompt")
        }),
        ("Metadata", {
            "fields": ("is_active", "created_by", "created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )


class MessageInline(admin.TabularInline):
    """Inline display for messages in session."""
    model = Message
    extra = 0
    readonly_fields = ["id", "role", "content", "message_type", "created_at"]
    fields = ["order", "role", "content", "message_type", "created_at"]
    ordering = ["order"]
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    """Admin configuration for Session model."""
    
    list_display = [
        "id", "user", "persona", "status", 
        "total_messages", "rating", "started_at"
    ]
    list_filter = ["status", "persona", "rating", "started_at"]
    search_fields = ["user__email", "persona__name", "title", "scenario"]
    ordering = ["-started_at"]
    readonly_fields = [
        "id", "total_messages", "total_duration_seconds", 
        "started_at", "ended_at"
    ]
    inlines = [MessageInline]
    
    fieldsets = (
        ("Thông tin phiên", {
            "fields": ("id", "user", "persona", "title", "scenario")
        }),
        ("Trạng thái", {
            "fields": ("status", "total_messages", "total_duration_seconds")
        }),
        ("Đánh giá", {
            "fields": ("rating", "feedback", "ai_feedback", "score"),
            "classes": ("collapse",)
        }),
        ("Thời gian", {
            "fields": ("started_at", "ended_at"),
            "classes": ("collapse",)
        }),
    )


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    """Admin configuration for Message model."""
    
    list_display = [
        "id", "session", "role", "content_preview", 
        "message_type", "created_at"
    ]
    list_filter = ["role", "message_type", "created_at"]
    search_fields = ["content", "session__user__email"]
    ordering = ["-created_at"]
    readonly_fields = ["id", "created_at"]
    
    fieldsets = (
        ("Thông tin tin nhắn", {
            "fields": ("id", "session", "order", "role", "content")
        }),
        ("Media", {
            "fields": ("message_type", "audio_url", "audio_duration_seconds"),
            "classes": ("collapse",)
        }),
        ("Metadata", {
            "fields": ("tokens_used", "created_at"),
            "classes": ("collapse",)
        }),
    )
    
    def content_preview(self, obj):
        """Show truncated content."""
        return obj.content[:80] + "..." if len(obj.content) > 80 else obj.content
    content_preview.short_description = "Nội dung"
