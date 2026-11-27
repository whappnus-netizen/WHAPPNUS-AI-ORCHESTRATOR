import asyncio

from app.api.schemas.requests import ChatRequest
from app.config import Settings
from app.core.errors import ProviderError
from app.core.orchestrator import Orchestrator
from app.core.router import select_candidates


class FakeProvider:
    def __init__(self, name, configured=True, error=None, response=None):
        self.name = name
        self.is_configured = configured
        self.error = error
        self.response = response or {"provider": name, "model": "fake-model", "content": "ok", "usage": {}}

    def get_capabilities(self):
        models = {
            "gemini": ["gemini-3.8-flash", "gemini-3.1-pro-preview"],
            "openai": ["gpt-4.1-mini"],
            "anthropic": ["claude-sonnet-4-5"],
        }
        return {"capabilities": ["text"], "models": models[self.name]}

    async def generate(self, **kwargs):
        if self.error:
            raise self.error
        return dict(self.response)

    async def health_check(self):
        return {"available": self.is_configured}

    def validate_configuration(self):
        return self.is_configured


class FakeRegistry:
    def __init__(self, providers):
        from app.core.circuit_breaker import CircuitBreaker
        self.items = {p.name: p for p in providers}
        self.breakers = {p.name: CircuitBreaker() for p in providers}

    def get(self, name):
        return self.items.get(name)

    def breaker(self, name):
        return self.breakers[name]


def request():
    return ChatRequest(
        organization_id="org-test",
        preferred_provider="gemini",
        task_type="customer_support",
        messages=[{"role": "user", "content": "Olá"}],
    )



def test_simple_task_selects_gemini_flash_model():
    settings = Settings(_env_file=None, gemini_api_key="configured")
    registry = FakeRegistry([FakeProvider("gemini")])
    body = request()
    candidates = select_candidates(body, registry, settings)
    assert candidates[0][1] == "gemini-3.8-flash"


def test_complex_task_selects_distinct_gemini_advanced_model():
    settings = Settings(_env_file=None, gemini_api_key="configured")
    registry = FakeRegistry([FakeProvider("gemini")])
    body = ChatRequest(
        organization_id="org-test",
        preferred_provider="gemini",
        task_type="complex",
        messages=[{"role": "user", "content": "Analisa detalhadamente esta situação."}],
    )
    candidates = select_candidates(body, registry, settings)
    assert candidates[0][1] == "gemini-3.1-pro-preview"


async def test_total_request_deadline_bounds_provider_and_fallback_work():
    settings = Settings(
        _env_file=None,
        gemini_api_key="configured",
        openai_api_key="configured",
        request_timeout_seconds=10,
        total_request_timeout_seconds=0.05,
        max_retries=0,
        fallback_provider_order="openai",
    )

    class SlowProvider(FakeProvider):
        async def generate(self, **kwargs):
            await asyncio.sleep(0.2)
            return dict(self.response)

    registry = FakeRegistry([SlowProvider("gemini"), FakeProvider("openai")])
    try:
        await Orchestrator(registry, settings).run(request())
        assert False, "expected total deadline error"
    except ProviderError as error:
        assert error.code == "ORCHESTRATOR_DEADLINE_EXCEEDED"
        assert error.retryable is True

async def test_auth_failure_falls_back_to_another_provider():
    settings = Settings(_env_file=None, gemini_api_key="configured", openai_api_key="configured", max_retries=0, fallback_provider_order="openai")
    registry = FakeRegistry([
        FakeProvider("gemini", error=ProviderError("PROVIDER_AUTH_ERROR", "bad key", False)),
        FakeProvider("openai"),
    ])
    result = await Orchestrator(registry, settings).run(request())
    assert result["provider"] == "openai"
    assert result["fallback_used"] is True
    assert result["fallback_chain"] == ["gemini", "openai"]


async def test_model_not_found_falls_back_without_retrying_same_provider():
    settings = Settings(_env_file=None, gemini_api_key="configured", openai_api_key="configured", max_retries=2, fallback_provider_order="openai")
    registry = FakeRegistry([
        FakeProvider("gemini", error=ProviderError("PROVIDER_MODEL_NOT_FOUND", "model missing", retryable=False, fallback_allowed=True, provider="gemini")),
        FakeProvider("openai"),
    ])
    result = await Orchestrator(registry, settings).run(request())
    assert result["provider"] == "openai"
    assert result["fallback_chain"] == ["gemini", "openai"]


async def test_non_retryable_request_error_can_still_stop_fallback_when_explicitly_forbidden():
    settings = Settings(_env_file=None, gemini_api_key="configured", openai_api_key="configured", max_retries=0, fallback_provider_order="openai")
    registry = FakeRegistry([
        FakeProvider("gemini", error=ProviderError("PROVIDER_REQUEST_INVALID", "request cannot be used by any provider", False, fallback_allowed=False)),
        FakeProvider("openai"),
    ])
    try:
        await Orchestrator(registry, settings).run(request())
        assert False, "expected ProviderError"
    except ProviderError as error:
        assert error.code == "PROVIDER_REQUEST_INVALID"
