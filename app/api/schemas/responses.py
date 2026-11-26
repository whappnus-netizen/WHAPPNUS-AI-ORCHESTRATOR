from typing import Any
from pydantic import BaseModel, Field


class Usage(BaseModel):
    input_tokens: int | None = None
    output_tokens: int | None = None
    total_tokens: int | None = None
    estimated_cost: float | None = None
    currency: str | None = None


class ChatResponse(BaseModel):
    request_id: str
    provider: str
    model: str
    content: str
    finish_reason: str | None = None
    usage: Usage = Field(default_factory=Usage)
    latency_ms: float
    fallback_used: bool = False
    fallback_chain: list[str] = Field(default_factory=list)
    structured_error: dict[str, Any] | None = None
