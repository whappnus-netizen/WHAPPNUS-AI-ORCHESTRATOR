from app.config import get_settings
from app.providers.registry import build_provider_registry

settings = get_settings()
providers = build_provider_registry(settings)
