def configured_models(settings) -> dict[str, list[str]]:
    return {
        'gemini': [settings.gemini_flash_model, settings.gemini_advanced_model],
        'openai': [settings.openai_model],
        'anthropic': [settings.anthropic_model],
    }
