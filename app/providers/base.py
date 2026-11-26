from abc import ABC, abstractmethod
from typing import Any


class BaseProvider(ABC):
    name: str
    is_configured: bool

    @abstractmethod
    async def generate(self, *, model: str, messages: list[dict[str, str]], system: str | None, max_tokens: int, temperature: float) -> dict[str, Any]: ...

    @abstractmethod
    async def health_check(self) -> dict[str, object]: ...

    @abstractmethod
    def validate_configuration(self) -> bool: ...

    @abstractmethod
    def get_capabilities(self) -> dict[str, object]: ...
