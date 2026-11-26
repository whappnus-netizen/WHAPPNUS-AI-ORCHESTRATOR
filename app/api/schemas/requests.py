import base64
from typing import Any, Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

class ContentPart(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type: Literal["text", "image", "audio", "document"]
    text: str | None = Field(default=None, max_length=200000)
    data: str | None = Field(default=None, max_length=21000000)
    mime_type: str | None = None

    @model_validator(mode="after")
    def validate_payload(self):
        if self.type == "text":
            if not self.text or self.data is not None or self.mime_type is not None:
                raise ValueError("Text parts require text only.")
            return self
        allowed = {
            "image": {"image/jpeg", "image/png", "image/webp", "image/gif"},
            "audio": {"audio/mpeg", "audio/wav", "audio/ogg", "audio/mp4", "audio/webm", "audio/flac"},
            "document": {"application/pdf"},
        }
        limits = {"image": 5, "audio": 15, "document": 10}
        if not self.data or self.mime_type not in allowed[self.type] or self.text is not None:
            raise ValueError(f"{self.type.title()} parts require base64 data and a supported MIME type.")
        try:
            decoded = base64.b64decode(self.data, validate=True)
        except Exception as exc:
            raise ValueError("Media data must be valid base64.") from exc
        if not decoded or len(decoded) > limits[self.type] * 1024 * 1024:
            raise ValueError(f"{self.type.title()} payload exceeds its size limit.")
        return self

class Message(BaseModel):
    model_config = ConfigDict(extra="forbid")
    role: Literal["system", "user", "assistant"]
    content: str | list[ContentPart]

    @field_validator("content")
    @classmethod
    def validate_content(cls, value):
        if isinstance(value, str):
            if not value or len(value) > 200000:
                raise ValueError("Message text must be between 1 and 200000 characters.")
        elif not value or len(value) > 16:
            raise ValueError("Multimodal messages must contain between 1 and 16 parts.")
        return value

class ChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    request_id: str | None = Field(default=None, max_length=128)
    organization_id: str = Field(min_length=1, max_length=128)
    conversation_id: str | None = Field(default=None, max_length=128)
    task_type: str = Field(default="general", max_length=64)
    messages: list[Message] = Field(min_length=1, max_length=100)
    system_instructions: str | None = Field(default=None, max_length=30000)
    preferred_provider: str | None = None
    preferred_model: str | None = None
    capabilities_required: list[str] = Field(default_factory=list)
    max_tokens: int = Field(default=1024, ge=1, le=16384)
    temperature: float = Field(default=0.4, ge=0, le=2)
    metadata: dict[str, Any] = Field(default_factory=dict)

class EstimateRequest(BaseModel):
    organization_id: str = Field(min_length=1, max_length=128)
    messages: list[Message] = Field(min_length=1, max_length=100)
    max_tokens: int = Field(default=1024, ge=1, le=16384)

class ValidateRequest(BaseModel):
    organization_id: str = Field(min_length=1, max_length=128)
    messages: list[Message] = Field(min_length=1, max_length=100)
