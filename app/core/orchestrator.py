import asyncio
from app.core.errors import NoProviderAvailable, ProviderError
from app.core.context_manager import fit_context
from app.core.router import select_candidates
from app.utils.retries import backoff

class Orchestrator:
    def __init__(self, registry, settings): self.registry,self.settings=registry,settings
    async def run(self, body):
        candidates=select_candidates(body,self.registry,self.settings)
        if not candidates: raise NoProviderAvailable()
        messages=fit_context([m.model_dump() for m in body.messages],self.settings.max_input_tokens)
        attempts=[]
        for provider,model in candidates:
            breaker=self.registry.breaker(provider.name)
            if breaker.is_open: continue
            for attempt in range(self.settings.max_retries + 1):
                if provider.name not in attempts: attempts.append(provider.name)
                try:
                    result=await asyncio.wait_for(provider.generate(model=model,messages=messages,system=body.system_instructions,max_tokens=min(body.max_tokens,self.settings.max_output_tokens),temperature=body.temperature),timeout=self.settings.request_timeout_seconds)
                    breaker.record_success()
                    result['fallback_used']=len(attempts)>1
                    result['fallback_chain']=attempts.copy()
                    return result
                except asyncio.TimeoutError:
                    error=ProviderError('PROVIDER_TIMEOUT','Provider request timed out.',True)
                except ProviderError as exc:
                    error=exc
                if not error.retryable:
                    raise error
                breaker.record_failure()
                if attempt < self.settings.max_retries:
                    await backoff(attempt)
                    continue
                break
        raise NoProviderAvailable()
