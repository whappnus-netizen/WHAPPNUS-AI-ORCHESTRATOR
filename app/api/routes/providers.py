from fastapi import APIRouter, Depends
from app.dependencies import providers
from app.security.authentication import require_api_key
router = APIRouter(tags=['providers'], dependencies=[Depends(require_api_key)])

@router.get('/providers')
async def list_providers():
    return [p.get_capabilities() | {'configured': p.is_configured} for p in providers.all()]

@router.get('/providers/health')
async def provider_health():
    return [await p.health_check() for p in providers.all()]
