"""
Database models for Voice Chat conversations.

Models:
- Persona: Hồ sơ phụ huynh (đặc điểm, phong cách giao tiếp)
- Session: Phiên luyện tập (một cuộc hội thoại)
- Message: Lịch sử hội thoại (từng tin nhắn trong session)
"""

import uuid
from django.db import models
from django.conf import settings


class Persona(models.Model):
    """
    Persona model - Hồ sơ phụ huynh cho mô phỏng hội thoại.
    
    Định nghĩa các đặc điểm của "phụ huynh ảo" mà người dùng sẽ luyện tập giao tiếp.
    """
    
    class PersonalityType(models.TextChoices):
        """Kiểu tính cách của persona."""
        FRIENDLY = "friendly", "Thân thiện"
        STRICT = "strict", "Nghiêm khắc"
        ANXIOUS = "anxious", "Lo lắng"
        DEMANDING = "demanding", "Đòi hỏi cao"
        SUPPORTIVE = "supportive", "Hỗ trợ"
        SKEPTICAL = "skeptical", "Hoài nghi"
        BUSY = "busy", "Bận rộn"
    
    class DifficultyLevel(models.TextChoices):
        """Mức độ khó của persona."""
        EASY = "easy", "Dễ"
        MEDIUM = "medium", "Trung bình"
        HARD = "hard", "Khó"
        EXPERT = "expert", "Chuyên gia"
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Basic info
    name = models.CharField(max_length=100, verbose_name="Tên persona")
    avatar = models.ImageField(
        upload_to="personas/avatars/", 
        blank=True, 
        null=True, 
        verbose_name="Ảnh đại diện"
    )
    description = models.TextField(verbose_name="Mô tả")
    
    # Persona characteristics
    personality_type = models.CharField(
        max_length=20,
        choices=PersonalityType.choices,
        default=PersonalityType.FRIENDLY,
        verbose_name="Kiểu tính cách"
    )
    difficulty_level = models.CharField(
        max_length=20,
        choices=DifficultyLevel.choices,
        default=DifficultyLevel.MEDIUM,
        verbose_name="Mức độ khó"
    )
    
    # Background story
    background = models.TextField(
        blank=True,
        verbose_name="Câu chuyện nền",
        help_text="Hoàn cảnh gia đình, nghề nghiệp, mối quan tâm của phụ huynh"
    )
    
    # Child info (context for the conversation)
    child_name = models.CharField(
        max_length=100, 
        blank=True, 
        verbose_name="Tên con",
        help_text="Tên của học sinh/con trong kịch bản"
    )
    child_age = models.PositiveIntegerField(
        blank=True, 
        null=True, 
        verbose_name="Tuổi con"
    )
    child_grade = models.CharField(
        max_length=50, 
        blank=True, 
        verbose_name="Lớp/Khối"
    )
    
    # Conversation style
    communication_style = models.TextField(
        blank=True,
        verbose_name="Phong cách giao tiếp",
        help_text="Cách nói chuyện, từ ngữ thường dùng, thái độ"
    )
    common_concerns = models.TextField(
        blank=True,
        verbose_name="Mối quan tâm thường gặp",
        help_text="Các vấn đề phụ huynh thường hỏi hoặc lo lắng"
    )
    
    # System prompt for AI
    system_prompt = models.TextField(
        verbose_name="System Prompt",
        help_text="Prompt gửi cho AI để đóng vai persona này"
    )
    
    # Metadata
    is_active = models.BooleanField(default=True, verbose_name="Đang hoạt động")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_personas",
        verbose_name="Người tạo"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Ngày tạo")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Ngày cập nhật")
    
    class Meta:
        verbose_name = "Persona"
        verbose_name_plural = "Personas"
        ordering = ["-created_at"]
    
    def __str__(self):
        return f"{self.name} ({self.get_personality_type_display()})"


class Session(models.Model):
    """
    Session model - Phiên luyện tập hội thoại.
    
    Mỗi session là một cuộc hội thoại hoàn chỉnh giữa user và persona.
    """
    
    class SessionStatus(models.TextChoices):
        """Trạng thái của session."""
        ACTIVE = "active", "Đang diễn ra"
        COMPLETED = "completed", "Hoàn thành"
        ABANDONED = "abandoned", "Bỏ dở"
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Relationships
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="sessions",
        verbose_name="Người dùng"
    )
    persona = models.ForeignKey(
        Persona,
        on_delete=models.CASCADE,
        related_name="sessions",
        verbose_name="Persona"
    )
    
    # Session info
    title = models.CharField(
        max_length=255, 
        blank=True, 
        verbose_name="Tiêu đề",
        help_text="Tự động tạo từ nội dung hội thoại nếu để trống"
    )
    scenario = models.TextField(
        blank=True,
        verbose_name="Kịch bản",
        help_text="Tình huống cụ thể của cuộc hội thoại"
    )
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=SessionStatus.choices,
        default=SessionStatus.ACTIVE,
        verbose_name="Trạng thái"
    )
    
    # Metrics
    total_messages = models.PositiveIntegerField(
        default=0, 
        verbose_name="Tổng số tin nhắn"
    )
    total_duration_seconds = models.PositiveIntegerField(
        default=0,
        verbose_name="Tổng thời gian (giây)"
    )
    
    # Feedback (after session)
    rating = models.PositiveSmallIntegerField(
        blank=True, 
        null=True,
        verbose_name="Đánh giá",
        help_text="1-5 sao"
    )
    feedback = models.TextField(
        blank=True, 
        verbose_name="Phản hồi",
        help_text="Nhận xét của người dùng về phiên luyện tập"
    )
    
    # AI evaluation
    ai_feedback = models.TextField(
        blank=True,
        verbose_name="Nhận xét từ AI",
        help_text="Đánh giá tự động từ AI về kỹ năng giao tiếp"
    )
    score = models.PositiveSmallIntegerField(
        blank=True,
        null=True,
        verbose_name="Điểm số",
        help_text="Điểm đánh giá từ AI (0-100)"
    )
    
    # Timestamps
    started_at = models.DateTimeField(auto_now_add=True, verbose_name="Bắt đầu lúc")
    ended_at = models.DateTimeField(
        blank=True, 
        null=True, 
        verbose_name="Kết thúc lúc"
    )
    
    class Meta:
        verbose_name = "Phiên luyện tập"
        verbose_name_plural = "Phiên luyện tập"
        ordering = ["-started_at"]
    
    def __str__(self):
        return f"Session {self.id} - {self.user.email} với {self.persona.name}"
    
    def calculate_duration(self):
        """Calculate session duration in seconds."""
        if self.ended_at and self.started_at:
            delta = self.ended_at - self.started_at
            return int(delta.total_seconds())
        return 0
    
    def save(self, *args, **kwargs):
        if self.ended_at:
            self.total_duration_seconds = self.calculate_duration()
        super().save(*args, **kwargs)


class Message(models.Model):
    """
    Message model - Lịch sử hội thoại.
    
    Lưu trữ từng tin nhắn trong một session.
    """
    
    class MessageRole(models.TextChoices):
        """Vai trò của người gửi tin nhắn."""
        USER = "user", "Người dùng"
        ASSISTANT = "assistant", "Phụ huynh (AI)"
        SYSTEM = "system", "Hệ thống"
    
    class MessageType(models.TextChoices):
        """Loại tin nhắn."""
        TEXT = "text", "Văn bản"
        VOICE = "voice", "Giọng nói"
        IMAGE = "image", "Hình ảnh"
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Relationship
    session = models.ForeignKey(
        Session,
        on_delete=models.CASCADE,
        related_name="messages",
        verbose_name="Phiên"
    )
    
    # Message content
    role = models.CharField(
        max_length=20,
        choices=MessageRole.choices,
        verbose_name="Vai trò"
    )
    content = models.TextField(verbose_name="Nội dung")
    
    # Message type and media
    message_type = models.CharField(
        max_length=20,
        choices=MessageType.choices,
        default=MessageType.TEXT,
        verbose_name="Loại tin nhắn"
    )
    audio_url = models.URLField(
        blank=True,
        verbose_name="URL audio",
        help_text="Link file audio nếu là tin nhắn voice"
    )
    audio_duration_seconds = models.FloatField(
        blank=True,
        null=True,
        verbose_name="Thời lượng audio (giây)"
    )
    
    # Metadata
    tokens_used = models.PositiveIntegerField(
        default=0,
        verbose_name="Tokens sử dụng",
        help_text="Số tokens AI đã sử dụng cho tin nhắn này"
    )
    
    # Ordering
    order = models.PositiveIntegerField(
        default=0,
        verbose_name="Thứ tự",
        help_text="Thứ tự tin nhắn trong session"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Thời gian gửi")
    
    class Meta:
        verbose_name = "Tin nhắn"
        verbose_name_plural = "Tin nhắn"
        ordering = ["session", "order", "created_at"]
    
    def __str__(self):
        content_preview = self.content[:50] + "..." if len(self.content) > 50 else self.content
        return f"[{self.get_role_display()}] {content_preview}"
    
    def save(self, *args, **kwargs):
        # Auto-increment order if not set
        if not self.order:
            last_message = Message.objects.filter(session=self.session).order_by("-order").first()
            self.order = (last_message.order + 1) if last_message else 1
        
        super().save(*args, **kwargs)
        
        # Update session message count
        self.session.total_messages = Message.objects.filter(session=self.session).count()
        self.session.save(update_fields=["total_messages"])
