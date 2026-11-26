import asyncio
import json
from app.core.context_manager import fit_context
from app.core.errors import NoProviderAvailable, ProviderError
from app.core.model_limits import model_limits
from app.core.router import select_candidates
from app.core.cost_manager import estimate_cost
from app.observability.request_metrics import ERRORS, FALLBACKS, LATENCY, REQUESTS
from app.utils.retries import backoff

class Orchestrator:
    def __init__(self, registry, settings):
        self.registry, self.settings = registry, settings

    async def run(self, body):
        candidates = select_candidates(body, self.registry, self.settings)
        if not candidates:
            raise NoProviderAvailable()
        attempted = []
        last_error = None
        for provider, model in candidates:
            breaker = self.registry.breaker(provider.name)
            if breaker.is_open:
                continue
            limits = model_limits(self.settings, provider.name, model)
            try:
                messages = fit_context([m.model_dump() for m in body.messages], min(limits["max_input_tokens"], self.settings.max_input_tokens))
            except ValueError as exc:
                raise ProviderError("CONTEXT_TOO_LARGE", str(exc), fallback_allowed=False) from exc
            output_limit = min(body.max_tokens, limits["max_output_tokens"], self.settings.max_output_tokens)
            for attempt in range(self.settings.max_retries + 1):
                if provider.name not in attempted:
                    attempted.append(provider.name)
                try:
                    async with asyncio.timeout(self.settings.request_timeout_seconds):
                        result = await provider.generate(model=model, messages=messages, system=body.system_instructions, max_tokens=output_limit, temperature=body.temperature)
                    breaker.record_success()
                    usage = result.get("usage") or {}
                    try:
                        pricing = json.loads(self.settings.model_pricing_json or "{}")
                    except (TypeError, ValueError):
                        pricing = {}
                    rates = pricing.get(f"{provider.name}:{model}", pricing.get(model, {}))
                    usage["estimated_cost"] = estimate_cost(usage.get("input_tokens"), usage.get("output_tokens"), rates)
                    usage["currency"] = self.settings.pricing_currency if usage["estimated_cost"] is not None else None
                    result["usage"] = usage
                    result["fallback_used"] = len(attempted) > 1
                    result["fallback_chain"] = attempted.copy()
                    REQUESTS.labels(provider.name, "success").inc()
                    LATENCY.labels(provider.name).observe(0)
                    if result["fallback_used"]:
                        FALLBACKS.inc()
                    return result
                except TimeoutError:
                    error = ProviderError("PROVIDER_TIMEOUT", "Provider request timed out.", True)
                except ProviderError as exc:
                    error = exc
                last_error = error
                ERRORS.labels(provider.name, error.code).inc()
                if error.retryable:
                    breaker.record_failure()
                    if attempt < self.settings.max_retries:
                        await backoff(attempt, retry_after=error.retry_after_seconds)
                        continue
                if not error.fallback_allowed:
                    REQUESTS.labels(provider.name, "error").inc()
                    raise error
                break
        if last_error:
            raise last_error
        raise NoProviderAvailable()
