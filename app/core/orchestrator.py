import asyncio
import json
import time

from app.core.context_manager import fit_context
from app.core.cost_manager import estimate_cost
from app.core.errors import NoProviderAvailable, ProviderError
from app.core.model_limits import model_limits
from app.core.router import select_candidates
from app.core.token_manager import estimate_tokens
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
        deadline = time.monotonic() + self.settings.total_request_timeout_seconds
        for provider, model in candidates:
            breaker = self.registry.breaker(provider.name)
            if breaker.is_open:
                continue

            limits = model_limits(self.settings, provider.name, model)
            try:
                system_tokens = estimate_tokens(body.system_instructions or "")
                available_input = min(limits["max_input_tokens"], self.settings.max_input_tokens) - system_tokens
                if available_input < 1:
                    raise ValueError("System instructions exceed the configured input context budget.")
                messages = fit_context([m.model_dump() for m in body.messages], available_input)
            except ValueError as exc:
                raise ProviderError("CONTEXT_TOO_LARGE", str(exc), fallback_allowed=False) from exc

            output_limit = min(body.max_tokens, limits["max_output_tokens"], self.settings.max_output_tokens)
            for attempt in range(self.settings.max_retries + 1):
                if provider.name not in attempted:
                    attempted.append(provider.name)
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    last_error = ProviderError(
                        "ORCHESTRATOR_DEADLINE_EXCEEDED",
                        "The total Orchestrator request deadline was exceeded.",
                        retryable=True,
                        fallback_allowed=True,
                        provider=provider.name,
                    )
                    break
                started = time.perf_counter()
                try:
                    async with asyncio.timeout(min(self.settings.request_timeout_seconds, remaining)):
                        result = await provider.generate(
                            model=model,
                            messages=messages,
                            system=body.system_instructions,
                            max_tokens=output_limit,
                            temperature=body.temperature,
                        )

                    content = result.get("content")
                    if not isinstance(content, str) or not content.strip():
                        raise ProviderError(
                            "PROVIDER_EMPTY_RESPONSE",
                            "Provider returned an empty completion.",
                            retryable=True,
                            fallback_allowed=True,
                            provider=provider.name,
                        )

                    LATENCY.labels(provider.name).observe(time.perf_counter() - started)
                    breaker.record_success()

                    usage = result.get("usage")
                    usage = dict(usage) if isinstance(usage, dict) else {}
                    try:
                        pricing = json.loads(self.settings.model_pricing_json or "{}")
                    except (TypeError, ValueError):
                        pricing = {}
                    if not isinstance(pricing, dict):
                        pricing = {}
                    rates = pricing.get(f"{provider.name}:{model}", pricing.get(model, {}))
                    if not isinstance(rates, dict):
                        rates = {}
                    estimated_cost = estimate_cost(
                        usage.get("input_tokens"),
                        usage.get("output_tokens"),
                        rates,
                    )
                    usage["estimated_cost"] = estimated_cost
                    usage["currency"] = self.settings.pricing_currency if estimated_cost is not None else None

                    result["usage"] = usage
                    result["fallback_used"] = len(attempted) > 1
                    result["fallback_chain"] = attempted.copy()
                    REQUESTS.labels(provider.name, "success").inc()
                    if result["fallback_used"]:
                        FALLBACKS.inc()
                    return result

                except TimeoutError:
                    deadline_exceeded = time.monotonic() >= deadline
                    error = ProviderError(
                        "ORCHESTRATOR_DEADLINE_EXCEEDED" if deadline_exceeded else "PROVIDER_TIMEOUT",
                        "The total Orchestrator request deadline was exceeded." if deadline_exceeded else "Provider request timed out.",
                        retryable=True,
                        fallback_allowed=True,
                        provider=provider.name,
                    )
                except ProviderError as exc:
                    error = exc

                LATENCY.labels(provider.name).observe(time.perf_counter() - started)
                last_error = error
                ERRORS.labels(provider.name, error.code).inc()
                if error.retryable:
                    breaker.record_failure()
                    retry_limit = self.settings.max_retries
                    if error.code == "PROVIDER_RATE_LIMIT":
                        retry_limit = min(retry_limit, self.settings.max_rate_limit_retries)
                    if attempt < retry_limit and time.monotonic() < deadline:
                        await backoff(attempt, retry_after=error.retry_after_seconds)
                        continue
                if not error.fallback_allowed:
                    REQUESTS.labels(provider.name, "error").inc()
                    raise error
                break

        if last_error:
            raise last_error
        raise NoProviderAvailable()
