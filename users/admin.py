"""
Admin configuration for User model.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth import get_user_model

User = get_user_model()


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Custom User Admin configuration.
    """
    list_display = [
        "email", "username", "first_name", "last_name",
        "is_verified", "is_active", "is_staff", "created_at"
    ]
    list_filter = ["is_verified", "is_active", "is_staff", "is_superuser", "created_at"]
    search_fields = ["email", "username", "first_name", "last_name", "phone"]
    ordering = ["-created_at"]
    
    fieldsets = (
        (None, {"fields": ("email", "username", "password")}),
        ("Thông tin cá nhân", {"fields": ("first_name", "last_name", "phone", "avatar")}),
        ("Trạng thái", {"fields": ("is_verified", "is_active", "is_staff", "is_superuser")}),
        ("Quyền hạn", {"fields": ("groups", "user_permissions")}),
        ("Thời gian", {"fields": ("last_login", "date_joined")}),
    )
    
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "username", "password1", "password2"),
        }),
    )
