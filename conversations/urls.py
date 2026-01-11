"""
URL configuration for Conversations API.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PersonaViewSet, SessionViewSet, MessageListView

app_name = "conversations"

router = DefaultRouter()
router.register(r"personas", PersonaViewSet, basename="persona")
router.register(r"sessions", SessionViewSet, basename="session")

urlpatterns = [
    path("", include(router.urls)),
    path("messages/", MessageListView.as_view(), name="message-list"),
]
