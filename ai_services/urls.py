"""
URL configuration for AI Services API.
"""

from django.urls import path
from .views import ChatView, ChatStreamView, AIHealthView

app_name = "ai_services"

urlpatterns = [
    path("chat/", ChatView.as_view(), name="chat"),
    path("chat/stream/", ChatStreamView.as_view(), name="chat-stream"),
    path("health/", AIHealthView.as_view(), name="health"),
]
