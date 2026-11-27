import json


def _positive_int(value, fallback: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError, OverflowError):
        return fallback
    return parsed if parsed > 0 else fallback


def model_limits(settings, provider: str, model: str) -> dict[str, int]:
    try:
        catalogue = json.loads(settings.model_limits_json or "{}")
    except (TypeError, ValueError):
        catalogue = {}
    if not isinstance(catalogue, dict):
        catalogue = {}
    entry = catalogue.get(f"{provider}:{model}", catalogue.get(model, {}))
    if not isinstance(entry, dict):
        entry = {}
    return {
        "max_input_tokens": _positive_int(entry.get("max_input_tokens"), settings.max_input_tokens),
        "max_output_tokens": _positive_int(entry.get("max_output_tokens"), settings.max_output_tokens),
    }
