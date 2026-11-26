def estimate_cost(input_tokens: int | None, output_tokens: int | None, pricing: dict | None = None):
    """Returns None unless a verified, explicitly configured price catalogue is supplied."""
    if not pricing or input_tokens is None or output_tokens is None:
        return None
    input_rate=pricing.get('input_per_million')
    output_rate=pricing.get('output_per_million')
    if input_rate is None or output_rate is None:
        return None
    return (input_tokens * float(input_rate) + output_tokens * float(output_rate)) / 1_000_000
