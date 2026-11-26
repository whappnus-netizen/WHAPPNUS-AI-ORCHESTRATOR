import base64

def openai_content(content):
    if isinstance(content, str):
        return content
    parts = []
    for part in content:
        item = part.model_dump() if hasattr(part, "model_dump") else part
        if item["type"] == "text":
            parts.append({"type": "text", "text": item["text"]})
        elif item["type"] == "image":
            uri = f"data:{item['mime_type']};base64,{item['data']}"
            parts.append({"type": "image_url", "image_url": {"url": uri, "detail": "auto"}})
        else:
            raise ValueError(f"OpenAI adapter does not support {item['type']} content.")
    return parts

def anthropic_content(content):
    if isinstance(content, str):
        return content
    parts = []
    for part in content:
        item = part.model_dump() if hasattr(part, "model_dump") else part
        if item["type"] == "text":
            parts.append({"type": "text", "text": item["text"]})
        elif item["type"] == "image":
            parts.append({"type": "image", "source": {"type": "base64", "media_type": item["mime_type"], "data": item["data"]}})
        elif item["type"] == "document":
            parts.append({"type": "document", "source": {"type": "base64", "media_type": item["mime_type"], "data": item["data"]}})
        else:
            raise ValueError(f"Anthropic adapter does not support {item['type']} content.")
    return parts

def gemini_content(messages, system):
    from google.genai import types
    contents = []
    for message in messages:
        role = message["role"]
        if role == "system":
            continue
        raw = message["content"]
        parts = []
        if isinstance(raw, str):
            parts.append(types.Part.from_text(text=raw))
        else:
            for part in raw:
                item = part.model_dump() if hasattr(part, "model_dump") else part
                if item["type"] == "text":
                    parts.append(types.Part.from_text(text=item["text"]))
                else:
                    parts.append(types.Part.from_bytes(data=base64.b64decode(item["data"]), mime_type=item["mime_type"]))
        contents.append(types.Content(role="model" if role == "assistant" else "user", parts=parts))
    return contents
