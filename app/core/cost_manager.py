import math


def estimate_cost(input_tokens: int | None, output_tokens: int | None, pricing: dict | None = None):
    """Return None unless valid, explicitly configured provider rates and usage are available."""
    if not isinstance(pricing, dict) or input_tokens is None or output_tokens is None:
        return None
    try:
        input_count = int(input_tokens)
        output_count = int(output_tokens)
        input_rate = float(pricing["input_per_million"])
        output_rate = float(pricing["output_per_million"])
    except (KeyError, TypeError, ValueError, OverflowError):
        return None
    if input_count < 0 or output_count < 0 or not math.isfinite(input_rate) or not math.isfinite(output_rate) or input_rate < 0 or output_rate < 0:
        return None
    return (input_count * input_rate + output_count * output_rate) / 1_000_000
