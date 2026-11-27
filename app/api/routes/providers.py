from fastapi import APIRouter, Depends, Response
from app.dependencies import providers
from app.observability.request_metrics import render_metrics
from app.security.authentication import require_api_key

router = APIRouter(tags=["providers"], dependencies=[Depends(require_api_key)])

@router.get("/providers")
async def list_providers():
    return [provider.get_capabilities() | {"configured": provider.is_configured} for provider in providers.all()]

@router.get("/providers/health")
async def provider_health():
    return [await provider.health_check() for provider in providers.all()]

@router.get("/metrics")
async def metrics():
    payload, content_type = render_metrics()
    return Response(content=payload, media_type=content_type)
