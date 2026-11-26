from app.api.schemas.requests import ChatRequest
from app.config import Settings
from app.core.errors import ProviderError
from app.core.orchestrator import Orchestrator

class FakeProvider:
    def __init__(self, name, configured=True, error=None, response=None):
        self.name = name
        self.is_configured = configured
        self.error = error
        self.response = response or {"provider": name, "model": "fake-model", "content": "ok", "usage": {}}
    def get_capabilities(self):
        return {"capabilities": ["text"]}
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
    return ChatRequest(organization_id="org-test", preferred_provider="gemini", task_type="customer_support", messages=[{"role":"user","content":"Olá"}])

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

async def test_non_retryable_request_error_stops_fallback():
    settings = Settings(_env_file=None, gemini_api_key="configured", openai_api_key="configured", max_retries=0, fallback_provider_order="openai")
    registry = FakeRegistry([
        FakeProvider("gemini", error=ProviderError("PROVIDER_REQUEST_INVALID", "bad input", False, fallback_allowed=False)),
        FakeProvider("openai"),
    ])
    try:
        await Orchestrator(registry, settings).run(request())
        assert False, "expected ProviderError"
    except ProviderError as error:
        assert error.code == "PROVIDER_REQUEST_INVALID"
