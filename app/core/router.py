from app.core.classifier import classify_task

def select_candidates(body, registry, settings):
    tier = classify_task(body.task_type, [message.model_dump() for message in body.messages])
    requested = (body.preferred_provider or settings.default_provider).lower()
    required = set(body.capabilities_required)
    for message in body.messages:
        if isinstance(message.content, list):
            required.update(part.type for part in message.content if part.type != "text")
    order = [requested]
    if settings.enable_fallback:
        order += settings.fallback_order + ["gemini", "openai", "anthropic"]
    seen = set()
    candidates = []
    for name in order:
        if name in seen:
            continue
        seen.add(name)
        provider = registry.get(name)
        if not provider or not provider.is_configured:
            continue
        model = body.preferred_model if name == requested and body.preferred_model else None
        if not model:
            if name == "gemini":
                model = settings.gemini_advanced_model if tier == "advanced" else settings.gemini_flash_model
            elif name == "openai":
                model = settings.openai_model
            else:
                model = settings.anthropic_model
        capabilities = provider.get_capabilities().get("capabilities", [])
        if any(capability not in capabilities for capability in required):
            continue
        candidates.append((provider, model))
    return candidates
