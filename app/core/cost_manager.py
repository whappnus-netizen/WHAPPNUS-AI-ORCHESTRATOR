import math


def estimate_cost(input_tokens: int | None, output_tokens: int | None, pricing: dict | None = None):
    """Return None unless valid, explicitly configured provider rates are available."""
    if not isinstance(pricing, dict) or input_tokens is None or output_tokens is None:
        return None
    input_rate = pricing.get("input_per_million")
    output_rate = pricing.get("output_per_million")
    if input_rate is None or output_rate is None:
        return None
    try:
        input_rate = float(input_rate)
        output_rate = float(output_rate)
    except (TypeError, ValueError, OverflowError):
        return None
    if not math.isfinite(input_rate) or not math.isfinite(output_rate) or input_rate < 0 or output_rate < 0:
        return None
    return (input_tokens * input_rate + output_tokens * output_rate) / 1_000_000
