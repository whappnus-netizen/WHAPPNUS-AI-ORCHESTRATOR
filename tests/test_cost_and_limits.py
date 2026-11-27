from types import SimpleNamespace

from app.core.cost_manager import estimate_cost
from app.core.model_limits import model_limits


def test_cost_is_not_invented_without_explicit_prices():
    assert estimate_cost(1000, 500) is None


def test_cost_uses_configured_per_million_prices():
    assert estimate_cost(1_000_000, 1_000_000, {"input_per_million": 1.0, "output_per_million": 2.0}) == 3.0


def test_invalid_pricing_is_non_fatal():
    assert estimate_cost(1000, 500, {"input_per_million": "not-a-price", "output_per_million": 2}) is None
    assert estimate_cost(1000, 500, {"input_per_million": -1, "output_per_million": 2}) is None


def test_model_specific_limits_override_defaults():
    settings = SimpleNamespace(
        model_limits_json='{"gemini:test-model":{"max_input_tokens":5000,"max_output_tokens":300}}',
        max_input_tokens=100000,
        max_output_tokens=4096,
    )
    assert model_limits(settings, "gemini", "test-model") == {"max_input_tokens": 5000, "max_output_tokens": 300}


def test_malformed_model_limits_fall_back_to_safe_defaults():
    settings = SimpleNamespace(
        model_limits_json='{"gemini:test-model":{"max_input_tokens":"bad","max_output_tokens":-2}}',
        max_input_tokens=100000,
        max_output_tokens=4096,
    )
    assert model_limits(settings, "gemini", "test-model") == {"max_input_tokens": 100000, "max_output_tokens": 4096}
