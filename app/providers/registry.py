from app.providers.base import BaseProvider
from app.providers.gemini.provider import GeminiProvider
from app.providers.openai.provider import OpenAIProvider
from app.providers.anthropic.provider import AnthropicProvider
from app.core.circuit_breaker import CircuitBreaker

class ProviderRegistry:
    def __init__(self, items: list[BaseProvider]):
        self._items = {p.name: p for p in items}
        self._breakers = {p.name: CircuitBreaker() for p in items}
    def get(self, name: str):
        return self._items.get(name)
    def all(self):
        return list(self._items.values())
    def breaker(self, name: str):
        return self._breakers[name]

def build_provider_registry(settings):
    return ProviderRegistry([GeminiProvider(settings), OpenAIProvider(settings), AnthropicProvider(settings)])
