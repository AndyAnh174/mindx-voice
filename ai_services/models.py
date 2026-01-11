"""
Data models for AI service requests and responses.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from enum import Enum


class MessageRole(str, Enum):
    """Role of the message sender."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


@dataclass
class ChatMessage:
    """A single message in the conversation."""
    
    role: MessageRole
    content: str
    
    def to_gemini_format(self) -> Dict[str, str]:
        """Convert to Gemini API format."""
        # Gemini uses 'user' and 'model' for roles
        role = "model" if self.role == MessageRole.ASSISTANT else self.role.value
        return {
            "role": role,
            "parts": [{"text": self.content}]
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> "ChatMessage":
        """Create from dictionary."""
        role = MessageRole(data.get("role", "user"))
        return cls(role=role, content=data.get("content", ""))


@dataclass
class PersonaContext:
    """Persona information for conversation context."""
    
    name: str
    personality_type: str
    description: str
    background: str = ""
    communication_style: str = ""
    common_concerns: str = ""
    child_name: str = ""
    child_age: Optional[int] = None
    child_grade: str = ""
    system_prompt: str = ""
    
    def build_system_message(self) -> str:
        """Build the system message for the AI."""
        if self.system_prompt:
            return self.system_prompt
        
        # Auto-generate system prompt if not provided
        prompt_parts = [
            f"Bạn đang đóng vai một phụ huynh tên là {self.name}.",
            f"Tính cách: {self.personality_type}.",
            f"Mô tả: {self.description}.",
        ]
        
        if self.background:
            prompt_parts.append(f"Hoàn cảnh: {self.background}.")
        
        if self.communication_style:
            prompt_parts.append(f"Phong cách giao tiếp: {self.communication_style}.")
        
        if self.common_concerns:
            prompt_parts.append(f"Các mối quan tâm: {self.common_concerns}.")
        
        if self.child_name:
            child_info = f"Con của bạn tên là {self.child_name}"
            if self.child_age:
                child_info += f", {self.child_age} tuổi"
            if self.child_grade:
                child_info += f", học lớp {self.child_grade}"
            prompt_parts.append(child_info + ".")
        
        prompt_parts.extend([
            "",
            "Hãy trả lời như một phụ huynh thực sự, với ngôn ngữ tự nhiên và phù hợp với tính cách đã được gán.",
            "Luôn duy trì vai diễn và không phá vỡ nhân vật.",
        ])
        
        return "\n".join(prompt_parts)
    
    @classmethod
    def from_persona_model(cls, persona) -> "PersonaContext":
        """Create from Persona Django model."""
        return cls(
            name=persona.name,
            personality_type=persona.get_personality_type_display(),
            description=persona.description,
            background=persona.background or "",
            communication_style=persona.communication_style or "",
            common_concerns=persona.common_concerns or "",
            child_name=persona.child_name or "",
            child_age=persona.child_age,
            child_grade=persona.child_grade or "",
            system_prompt=persona.system_prompt,
        )


@dataclass 
class GenerationParams:
    """Parameters for text generation."""
    
    max_tokens: int = 2048
    temperature: float = 0.7
    top_p: float = 0.95
    top_k: int = 40
    stop_sequences: List[str] = field(default_factory=list)
    
    def to_gemini_config(self) -> Dict[str, Any]:
        """Convert to Gemini generation config."""
        config = {
            "max_output_tokens": self.max_tokens,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "top_k": self.top_k,
        }
        if self.stop_sequences:
            config["stop_sequences"] = self.stop_sequences
        return config


@dataclass
class GenerationRequest:
    """Request for text generation."""
    
    prompt: str
    history: List[ChatMessage] = field(default_factory=list)
    persona: Optional[PersonaContext] = None
    params: GenerationParams = field(default_factory=GenerationParams)
    stream: bool = False
    
    def get_full_history(self) -> List[ChatMessage]:
        """Get history with system message prepended if persona exists."""
        messages = []
        
        if self.persona:
            system_msg = ChatMessage(
                role=MessageRole.SYSTEM,
                content=self.persona.build_system_message()
            )
            messages.append(system_msg)
        
        messages.extend(self.history)
        
        # Add current prompt
        messages.append(ChatMessage(role=MessageRole.USER, content=self.prompt))
        
        return messages


@dataclass
class GenerationResponse:
    """Response from text generation."""
    
    content: str
    finish_reason: str = "stop"
    tokens_used: int = 0
    model: str = ""
    
    # Metadata
    latency_ms: float = 0.0
    cached: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "content": self.content,
            "finish_reason": self.finish_reason,
            "tokens_used": self.tokens_used,
            "model": self.model,
            "latency_ms": self.latency_ms,
            "cached": self.cached,
        }


@dataclass
class StreamChunk:
    """A chunk of streamed response."""
    
    content: str
    is_final: bool = False
    tokens_used: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "content": self.content,
            "is_final": self.is_final,
            "tokens_used": self.tokens_used,
        }
