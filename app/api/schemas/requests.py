from typing import Any, Literal
from pydantic import BaseModel, ConfigDict, Field


class Message(BaseModel):
    model_config = ConfigDict(extra='forbid')
    role: Literal['system', 'user', 'assistant']
    content: str = Field(min_length=1, max_length=200000)


class ChatRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    request_id: str | None = Field(default=None, max_length=128)
    organization_id: str = Field(min_length=1, max_length=128)
    conversation_id: str | None = Field(default=None, max_length=128)
    task_type: str = Field(default='general', max_length=64)
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
