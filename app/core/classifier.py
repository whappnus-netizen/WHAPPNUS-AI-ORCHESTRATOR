def classify_task(task_type: str, messages: list[dict]) -> str:
    text_parts = []
    for message in messages:
        content = message.get("content", "")
        if isinstance(content, list):
            text_parts.extend(part.get("text", "") for part in content if isinstance(part, dict) and part.get("type") == "text")
        elif isinstance(content, str):
            text_parts.append(content)
    text = " ".join(text_parts).lower()
    if task_type.lower() in {"reasoning", "analysis", "complex", "strategy"} or any(
        phrase in text
        for phrase in ("analyze deeply", "compare alternatives", "step by step", "raciocina detalhadamente")
    ):
        return "advanced"
    return "flash"
