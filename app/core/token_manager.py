def estimate_tokens(text: str) -> int:
    # Conservative rough estimate only; provider tokenizers remain authoritative.
    return max(1, (len(text) + 3) // 4)


def estimate_messages_tokens(messages: list[dict[str, str]]) -> int:
    return sum(estimate_tokens(m.get('content', '')) + 4 for m in messages)
