import time
import uuid
from fastapi import APIRouter, Depends, HTTPException
from app.api.schemas.requests import ChatRequest, EstimateRequest, ValidateRequest
from app.api.schemas.responses import ChatResponse
from app.core.orchestrator import Orchestrator
from app.dependencies import providers, settings
from app.security.authentication import require_api_key
router = APIRouter(prefix='/chat', tags=['chat'], dependencies=[Depends(require_api_key)])

@router.post('/completions', response_model=ChatResponse)
async def completions(body: ChatRequest):
    started = time.perf_counter()
    request_id = body.request_id or str(uuid.uuid4())
    try:
        result = await Orchestrator(providers, settings).run(body)
    except Exception as exc:
        raise HTTPException(status_code=503, detail={'code': 'ORCHESTRATION_FAILED', 'request_id': request_id}) from exc
    return ChatResponse(request_id=request_id, provider=result['provider'], model=result['model'], content=result['content'], finish_reason=result.get('finish_reason'), usage=result.get('usage', {}), latency_ms=(time.perf_counter()-started)*1000, fallback_used=result.get('fallback_used', False), fallback_chain=result.get('fallback_chain', []))

@router.post('/estimate')
async def estimate(body: EstimateRequest):
    chars = sum(len(m.content) for m in body.messages)
    return {'estimated_input_tokens': max(1, chars // 4), 'requested_output_tokens': body.max_tokens, 'note': 'Character-based estimate; provider tokenization may differ. Pricing is not configured.'}

@router.post('/validate')
async def validate(body: ValidateRequest):
    return {'valid': True, 'message_count': len(body.messages), 'organization_id': body.organization_id}
