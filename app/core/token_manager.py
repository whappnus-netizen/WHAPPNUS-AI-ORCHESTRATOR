def estimate_tokens(content) -> int:
    """Approximate text tokens; binary payloads use coarse modality estimates, not base64 length."""
    if isinstance(content, str):
        return max(1, (len(content) + 3) // 4)
    if isinstance(content, list):
        total = 0
        estimates = {"image": 1024, "audio": 2000, "document": 3000}
        for part in content:
            item = part.model_dump() if hasattr(part, "model_dump") else part
            if item.get("type") in estimates:
                total += estimates[item["type"]]
            else:
                total += estimate_tokens(item.get("text", ""))
        return max(1, total)
    return 1

def estimate_messages_tokens(messages: list[dict]) -> int:
    return sum(estimate_tokens(message.get("content", "")) + 4 for message in messages)
