import pytest

from app.api.schemas.requests import ChatRequest
from app.config import Settings
from app.core.errors import ProviderError
from app.core.router import select_candidates


class Provider:
    def __init__(self, name, capabilities):
        self.name, self.capabilities, self.is_configured = name, capabilities, True

    def get_capabilities(self):
        models = {
            "gemini": ["gemini-3.8-flash"],
            "openai": ["gpt-4.1-mini"],
            "anthropic": ["claude-sonnet-4-5"],
        }
        return {"capabilities": self.capabilities, "models": models[self.name]}


class Registry:
    def __init__(self):
        self.providers = {
            "gemini": Provider("gemini", ["text", "image", "audio", "document"]),
            "openai": Provider("openai", ["text", "image"]),
            "anthropic": Provider("anthropic", ["text", "image", "document"]),
        }

    def get(self, name):
        return self.providers.get(name)


def test_audio_payload_only_routes_to_audio_capable_provider():
    settings = Settings(_env_file=None, default_provider="openai", enable_fallback=True, fallback_provider_order="anthropic,gemini")
    body = ChatRequest(organization_id="org", messages=[{"role": "user", "content": [{"type": "audio", "mime_type": "audio/mpeg", "data": "ZmFrZQ=="}]}])
    candidates = select_candidates(body, Registry(), settings)
    assert [provider.name for provider, _ in candidates] == ["gemini"]


def test_pdf_payload_routes_to_gemini_and_anthropic():
    settings = Settings(_env_file=None, default_provider="openai", enable_fallback=True, fallback_provider_order="anthropic,gemini")
    body = ChatRequest(organization_id="org", messages=[{"role": "user", "content": [{"type": "document", "mime_type": "application/pdf", "data": "JVBERi1mYWtl"}]}])
    candidates = select_candidates(body, Registry(), settings)
    assert {provider.name for provider, _ in candidates} == {"gemini", "anthropic"}


def test_explicit_unknown_model_fails_clearly_instead_of_silent_provider_switch():
    settings = Settings(_env_file=None, default_provider="gemini", gemini_api_key="configured", enable_fallback=True)
    body = ChatRequest(
        organization_id="org",
        preferred_provider="gemini",
        preferred_model="gemini-model-does-not-exist",
        messages=[{"role": "user", "content": "Olá"}],
    )
    with pytest.raises(ProviderError) as error:
        select_candidates(body, Registry(), settings)
    assert error.value.code == "MODEL_NOT_CONFIGURED"
