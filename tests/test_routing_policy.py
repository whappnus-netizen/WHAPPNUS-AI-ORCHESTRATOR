from types import SimpleNamespace

from app.core.router import select_candidates


class FakeMessage:
    def __init__(self, content):
        self.content = content

    def model_dump(self):
        return {"role": "user", "content": self.content}


class FakeProvider:
    def __init__(self, name, models):
        self.name = name
        self.is_configured = True
        self.models = models

    def get_capabilities(self):
        return {"models": self.models, "capabilities": ["text"]}


class FakeRegistry:
    def __init__(self, providers):
        self.providers = providers

    def get(self, name):
        return self.providers.get(name)


def make_settings(*, advanced_enabled=False, fallback_order=None):
    return SimpleNamespace(
        default_provider="gemini",
        default_model="",
        enable_fallback=True,
        fallback_order=fallback_order or [],
        gemini_primary_model="gemini-3.1-flash-lite",
        gemini_advanced_model="gemini-3.1-pro-preview",
        gemini_advanced_enabled=advanced_enabled,
        openai_model="gpt-4.1-mini",
        anthropic_model="claude-sonnet-4-5",
    )


def make_body(*, task_type="customer_support", preferred_provider=None, preferred_model=None):
    return SimpleNamespace(
        task_type=task_type,
        messages=[FakeMessage("Analisa detalhadamente esta situação" if task_type == "complex" else "Olá")],
        capabilities_required=["text"],
        preferred_provider=preferred_provider,
        preferred_model=preferred_model,
    )


def make_registry():
    return FakeRegistry({
        "gemini": FakeProvider("gemini", ["gemini-3.1-flash-lite", "gemini-3.1-pro-preview"]),
        "openai": FakeProvider("openai", ["gpt-4.1-mini"]),
        "anthropic": FakeProvider("anthropic", ["claude-sonnet-4-5"]),
    })


def test_simple_customer_support_uses_flash_lite_primary():
    candidates = select_candidates(make_body(), make_registry(), make_settings())
    assert [(provider.name, model) for provider, model in candidates] == [
        ("gemini", "gemini-3.1-flash-lite")
    ]


def test_complex_task_uses_flash_lite_while_advanced_tier_is_disabled():
    candidates = select_candidates(make_body(task_type="complex"), make_registry(), make_settings())
    assert [(provider.name, model) for provider, model in candidates] == [
        ("gemini", "gemini-3.1-flash-lite")
    ]


def test_complex_task_uses_pro_only_after_advanced_flag_is_enabled():
    candidates = select_candidates(
        make_body(task_type="complex"),
        make_registry(),
        make_settings(advanced_enabled=True),
    )
    assert [(provider.name, model) for provider, model in candidates] == [
        ("gemini", "gemini-3.1-pro-preview")
    ]


def test_explicit_legacy_pro_pin_is_safely_downgraded_while_advanced_is_disabled():
    candidates = select_candidates(
        make_body(preferred_model="gemini-3.1-pro-preview"),
        make_registry(),
        make_settings(),
    )
    assert [(provider.name, model) for provider, model in candidates] == [
        ("gemini", "gemini-3.1-flash-lite")
    ]


def test_legacy_flash_model_pin_is_mapped_to_flash_lite_primary():
    candidates = select_candidates(
        make_body(preferred_model="gemini-3.8-flash"),
        make_registry(),
        make_settings(),
    )
    assert [(provider.name, model) for provider, model in candidates] == [
        ("gemini", "gemini-3.1-flash-lite")
    ]


def test_fallback_is_not_inferred_from_configured_credentials():
    candidates = select_candidates(make_body(), make_registry(), make_settings(fallback_order=[]))
    assert [provider.name for provider, _ in candidates] == ["gemini"]


def test_only_explicitly_allowlisted_fallback_providers_are_candidates():
    candidates = select_candidates(
        make_body(),
        make_registry(),
        make_settings(fallback_order=["openai"]),
    )
    assert [provider.name for provider, _ in candidates] == ["gemini", "openai"]
