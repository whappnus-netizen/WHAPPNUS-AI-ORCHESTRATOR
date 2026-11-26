import json

DEFAULT_LIMITS = {"max_input_tokens": 100000, "max_output_tokens": 4096}

def model_limits(settings, provider: str, model: str) -> dict[str, int]:
    try:
        catalogue = json.loads(settings.model_limits_json or "{}")
    except (TypeError, ValueError):
        catalogue = {}
    entry = catalogue.get(f"{provider}:{model}", catalogue.get(model, {}))
    if not isinstance(entry, dict):
        entry = {}
    return {
        "max_input_tokens": max(1, int(entry.get("max_input_tokens", settings.max_input_tokens))),
        "max_output_tokens": max(1, int(entry.get("max_output_tokens", settings.max_output_tokens))),
    }
