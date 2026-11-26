import json

def estimate_tokens(text: str | list | dict) -> int:
    # Rough preflight estimate only; image payload tokens are provider-specific and usage is authoritative.
    if not isinstance(text, str):
        text = json.dumps(text, ensure_ascii=False, separators=(",", ":"))
    return max(1, (len(text) + 3) // 4)

def estimate_messages_tokens(messages: list[dict]) -> int:
    return sum(estimate_tokens(message.get("content", "")) + 4 for message in messages)
