from app.core.classifier import classify_task

def select_candidates(body, registry, settings):
    tier=classify_task(body.task_type,[m.model_dump() for m in body.messages])
    requested=(body.preferred_provider or settings.default_provider).lower()
    order=[requested]
    if settings.enable_fallback: order += settings.fallback_order + ['gemini','openai','anthropic']
    seen=set(); candidates=[]
    for name in order:
        if name in seen: continue
        seen.add(name); provider=registry.get(name)
        if not provider or not provider.is_configured: continue
        model=body.preferred_model if name==requested and body.preferred_model else None
        if not model:
            if name=='gemini':
                model=settings.gemini_advanced_model if tier=='advanced' else settings.gemini_flash_model
            elif name=='openai': model=settings.openai_model
            else: model=settings.anthropic_model
        if any(cap not in provider.get_capabilities().get('capabilities',[]) for cap in body.capabilities_required): continue
        candidates.append((provider,model))
    return candidates
