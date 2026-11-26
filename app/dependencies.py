from app.config import get_settings
from app.providers.registry import build_provider_registry
from app.security.rate_limiter import OrganizationRateLimiter

settings = get_settings()
providers = build_provider_registry(settings)
rate_limiter = OrganizationRateLimiter(
    redis_url=settings.redis_url.get_secret_value(),
    limit=settings.rate_limit_per_minute,
    window_seconds=settings.rate_limit_window_seconds,
    environment=settings.app_env,
)
