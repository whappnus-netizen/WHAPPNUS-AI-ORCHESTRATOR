from app.core.errors import NoProviderAvailable, ProviderError
from app.core.router import select_candidates

class Orchestrator:
    def __init__(self, registry, settings): self.registry,self.settings=registry,settings
    async def run(self, body):
        candidates=select_candidates(body,self.registry,self.settings)
        if not candidates: raise NoProviderAvailable()
        messages=[m.model_dump() for m in body.messages]; attempts=[]
        for provider,model in candidates:
            attempts.append(provider.name)
            try:
                result=await provider.generate(model=model,messages=messages,system=body.system_instructions,max_tokens=min(body.max_tokens,self.settings.max_output_tokens),temperature=body.temperature)
                result['fallback_used']=len(attempts)>1; result['fallback_chain']=attempts
                return result
            except ProviderError as exc:
                if not exc.retryable: raise
        raise NoProviderAvailable()
