def estimate_tokens(content) -> int:
    """Approximate text tokens; image payloads use a conservative fixed estimate, never base64 length."""
    if isinstance(content, str):
        return max(1, (len(content) + 3) // 4)
    if isinstance(content, list):
        total = 0
        for part in content:
            item = part.model_dump() if hasattr(part, "model_dump") else part
            if item.get("type") == "image":
                total += 1024
            else:
                total += estimate_tokens(item.get("text", ""))
        return max(1, total)
    return 1

def estimate_messages_tokens(messages: list[dict]) -> int:
    return sum(estimate_tokens(message.get("content", "")) + 4 for message in messages)
