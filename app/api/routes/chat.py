import json
import time
import uuid
from fastapi import APIRouter, Depends, Header, HTTPException
from app.api.schemas.requests import ChatRequest, EstimateRequest, ValidateRequest
from app.api.schemas.responses import ChatResponse
from app.core.cost_manager import estimate_cost
from app.core.model_limits import model_limits
from app.core.orchestrator import Orchestrator
from app.core.token_manager import estimate_messages_tokens
from app.dependencies import providers, rate_limiter, settings
from app.security.authentication import require_api_key
from app.security.tenant_auth import verify_tenant_signature

router = APIRouter(prefix="/chat", tags=["chat"], dependencies=[Depends(require_api_key)])

async def authorize_tenant(organization_id: str, timestamp: str | None, signature: str | None) -> None:
    verify_tenant_signature(organization_id=organization_id, timestamp=timestamp, signature=signature, secret=settings.tenant_signing_secret.get_secret_value())
    await rate_limiter.enforce(organization_id)

@router.post("/completions", response_model=ChatResponse)
async def completions(body: ChatRequest, x_tenant_timestamp: str | None = Header(default=None), x_tenant_signature: str | None = Header(default=None)):
    await authorize_tenant(body.organization_id, x_tenant_timestamp, x_tenant_signature)
    started = time.perf_counter()
    request_id = body.request_id or str(uuid.uuid4())
    try:
        result = await Orchestrator(providers, settings).run(body)
    except Exception as exc:
        if hasattr(exc, "code"):
            raise HTTPException(status_code=503, detail={"code": exc.code, "request_id": request_id}) from exc
        raise
    return ChatResponse(request_id=request_id, provider=result["provider"], model=result["model"], content=result["content"], finish_reason=result.get("finish_reason"), usage=result.get("usage", {}), latency_ms=(time.perf_counter() - started) * 1000, fallback_used=result.get("fallback_used", False), fallback_chain=result.get("fallback_chain", []))

@router.post("/estimate")
async def estimate(body: EstimateRequest, x_tenant_timestamp: str | None = Header(default=None), x_tenant_signature: str | None = Header(default=None)):
    await authorize_tenant(body.organization_id, x_tenant_timestamp, x_tenant_signature)
    tokens = estimate_messages_tokens([m.model_dump() for m in body.messages])
    provider = settings.default_provider
    model = settings.default_model or (settings.gemini_flash_model if provider == "gemini" else settings.openai_model if provider == "openai" else settings.anthropic_model)
    limits = model_limits(settings, provider, model)
    try:
        catalogue = json.loads(settings.model_pricing_json or "{}")
    except (TypeError, ValueError):
        catalogue = {}
    pricing = catalogue.get(f"{provider}:{model}", catalogue.get(model, {}))
    cost = estimate_cost(tokens, body.max_tokens, pricing)
    return {"estimated_input_tokens": tokens, "requested_output_tokens": min(body.max_tokens, limits["max_output_tokens"]), "model": model, "within_model_input_limit": tokens <= limits["max_input_tokens"], "estimated_cost": cost, "currency": settings.pricing_currency if cost is not None else None, "note": "Token count is an estimate; provider tokenization and final usage are authoritative."}

@router.post("/validate")
async def validate(body: ValidateRequest, x_tenant_timestamp: str | None = Header(default=None), x_tenant_signature: str | None = Header(default=None)):
    await authorize_tenant(body.organization_id, x_tenant_timestamp, x_tenant_signature)
    return {"valid": True, "message_count": len(body.messages)}
