from app.core.errors import ProviderError
from app.core.provider_errors import normalize_provider_exception
from app.providers.base import BaseProvider

class AnthropicProvider(BaseProvider):
    name='anthropic'
    def __init__(self, settings):
        self.settings=settings
        self.is_configured=bool(settings.anthropic_api_key.get_secret_value())
        self.client=None
        if self.is_configured:
            from anthropic import AsyncAnthropic
            self.client=AsyncAnthropic(api_key=settings.anthropic_api_key.get_secret_value(),timeout=settings.request_timeout_seconds,max_retries=0)
    def validate_configuration(self): return self.is_configured
    def get_capabilities(self): return {'provider':self.name,'models':[self.settings.anthropic_model],'capabilities':['text'],'configured':self.is_configured}
    async def health_check(self): return {'provider':self.name,'available':self.is_configured,'status':'configured' if self.is_configured else 'missing_credentials'}
    async def generate(self, *, model, messages, system, max_tokens, temperature):
        if not self.client: raise ProviderError('PROVIDER_UNAVAILABLE','Anthropic credentials are not configured.')
        try:
            # Anthropic accepts only user/assistant messages; system instructions are a separate field.
            clean=[m for m in messages if m['role'] in ('user','assistant')]
            response=await self.client.messages.create(model=model,max_tokens=max_tokens,temperature=temperature,system=system or '',messages=clean)
            content='\n'.join(block.text for block in response.content if hasattr(block,'text'))
            return {'provider':self.name,'model':model,'content':content,'finish_reason':response.stop_reason,'usage':{'input_tokens':response.usage.input_tokens,'output_tokens':response.usage.output_tokens}}
        except Exception as exc: raise normalize_provider_exception(exc) from exc
