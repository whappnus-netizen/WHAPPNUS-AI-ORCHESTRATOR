from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.dependencies import providers, rate_limiter, settings

router = APIRouter(tags=["health"])


@router.get("/health")
async def health():
    # Liveness only: the process can serve HTTP requests.
    return {"status": "ok", "service": "whappnus-ai-orchestrator"}


@router.get("/ready")
async def ready():
    configured = [provider.name for provider in providers.all() if provider.is_configured]
    production = settings.app_env.lower() in {"production", "prod"}
    security_ready = bool(
        settings.orchestrator_api_key.get_secret_value()
        and settings.tenant_signing_secret.get_secret_value()
    )
    redis_ready = await rate_limiter.health_check()
    checks = {
        "providers": bool(configured),
        "security": security_ready if production else True,
        "redis": redis_ready,
    }
    is_ready = all(checks.values())
    payload = {
        "status": "ready" if is_ready else "degraded",
        "service": "whappnus-ai-orchestrator",
        "configured_providers": configured,
        "checks": checks,
    }
    return JSONResponse(content=payload, status_code=200 if is_ready else 503)
