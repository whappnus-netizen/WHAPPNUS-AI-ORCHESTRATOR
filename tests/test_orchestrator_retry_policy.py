import pytest

from app.core.errors import ProviderError
from app.core.orchestrator import Orchestrator
from app.core.circuit_breaker import CircuitBreaker


class FakeMessage:
    content = "Olá"

    def model_dump(self):
        return {"role": "user", "content": self.content}


class FakeProvider:
    name = "gemini"
    is_configured = True

    def __init__(self, error):
        self.error = error
        self.calls = 0

    def get_capabilities(self):
        return {"models": ["gemini-3.1-flash-lite"], "capabilities": ["text"]}

    async def generate(self, **kwargs):
        self.calls += 1
        raise self.error


class FakeRegistry:
    def __init__(self, provider):
        self.provider = provider
        self._breaker = CircuitBreaker(failure_threshold=5)

    def get(self, name):
        return self.provider if name == "gemini" else None

    def breaker(self, provider):
        return self._breaker


def make_settings():
    return type("Settings", (), {
        "default_provider": "gemini",
        "default_model": "",
        "enable_fallback": False,
        "fallback_order": [],
        "gemini_primary_model": "gemini-3.1-flash-lite",
        "gemini_advanced_model": "gemini-3.1-pro-preview",
        "gemini_advanced_enabled": False,
        "openai_model": "gpt-4.1-mini",
        "anthropic_model": "claude-sonnet-4-5",
        "total_request_timeout_seconds": 5,
        "request_timeout_seconds": 1,
        "max_retries": 3,
        "max_rate_limit_retries": 1,
        "max_input_tokens": 1000,
        "max_output_tokens": 100,
        "model_limits_json": "{}",
        "model_pricing_json": "{}",
        "pricing_currency": "USD",
    })()


def make_body():
    return type("Body", (), {
        "task_type": "customer_support",
        "messages": [FakeMessage()],
        "capabilities_required": ["text"],
        "preferred_provider": None,
        "preferred_model": None,
        "system_instructions": "",
        "max_tokens": 20,
        "temperature": 0,
    })()


@pytest.mark.asyncio
async def test_rate_limit_uses_smaller_retry_budget(monkeypatch):
    async def no_wait(*args, **kwargs):
        return None

    monkeypatch.setattr("app.core.orchestrator.backoff", no_wait)
    provider = FakeProvider(ProviderError(
        "PROVIDER_RATE_LIMIT", "Rate limited", retryable=True, provider="gemini"
    ))
    orchestrator = Orchestrator(FakeRegistry(provider), make_settings())

    with pytest.raises(ProviderError) as caught:
        await orchestrator.run(make_body())

    assert caught.value.code == "PROVIDER_RATE_LIMIT"
    assert provider.calls == 2  # initial attempt + one rate-limit retry


@pytest.mark.asyncio
async def test_quota_exhaustion_is_not_retried(monkeypatch):
    async def no_wait(*args, **kwargs):
        return None

    monkeypatch.setattr("app.core.orchestrator.backoff", no_wait)
    provider = FakeProvider(ProviderError(
        "PROVIDER_QUOTA_EXHAUSTED",
        "Quota exhausted",
        retryable=False,
        fallback_allowed=True,
        provider="gemini",
    ))
    orchestrator = Orchestrator(FakeRegistry(provider), make_settings())

    with pytest.raises(ProviderError) as caught:
        await orchestrator.run(make_body())

    assert caught.value.code == "PROVIDER_QUOTA_EXHAUSTED"
    assert provider.calls == 1
