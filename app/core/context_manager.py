from app.core.token_manager import estimate_messages_tokens


def fit_context(messages: list[dict[str, str]], max_input_tokens: int) -> list[dict[str, str]]:
    """Keep the newest complete messages within a rough token budget; never split content."""
    selected=[]
    used=0
    for message in reversed(messages):
        cost=estimate_messages_tokens([message])
        if used + cost > max_input_tokens:
            if not selected:
                raise ValueError('A single message exceeds the configured input context budget.')
            break
        selected.append(message)
        used += cost
    return list(reversed(selected))
