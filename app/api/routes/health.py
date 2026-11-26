from fastapi import APIRouter
from app.dependencies import providers
router = APIRouter(tags=['health'])

@router.get('/health')
async def health():
    return {'status': 'ok', 'service': 'whappnus-ai-orchestrator'}

@router.get('/ready')
async def ready():
    configured = [p.name for p in providers.all() if p.is_configured]
    return {'status': 'ready' if configured else 'degraded', 'configured_providers': configured}
