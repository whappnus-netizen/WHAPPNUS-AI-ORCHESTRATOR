from app.core.errors import ProviderError
from app.core.provider_errors import normalize_provider_exception
from app.providers.base import BaseProvider
from app.providers.multimodal import openai_content


class OpenAIProvider(BaseProvider):
    name = "openai"

    def __init__(self, settings):
        self.settings = settings
        self.is_configured = bool(settings.openai_api_key.get_secret_value())
        self.client = None
        if self.is_configured:
            from openai import AsyncOpenAI
            self.client = AsyncOpenAI(
                api_key=settings.openai_api_key.get_secret_value(),
                timeout=settings.request_timeout_seconds,
                max_retries=0,
            )

    def validate_configuration(self):
        return self.is_configured

    def get_capabilities(self):
        models = [self.settings.openai_model]
        if self.settings.default_provider == self.name and self.settings.default_model:
            models.append(self.settings.default_model)
        return {
            "provider": self.name,
            "models": list(dict.fromkeys(models)),
            "capabilities": ["text", "image"],
            "configured": self.is_configured,
        }

    async def health_check(self):
        return {
            "provider": self.name,
            "available": self.is_configured,
            "status": "configured" if self.is_configured else "missing_credentials",
        }

    async def generate(self, *, model, messages, system, max_tokens, temperature):
        if not self.client:
            raise ProviderError("PROVIDER_UNAVAILABLE", "OpenAI credentials are not configured.")
        payload = ([{"role": "system", "content": system}] if system else [])
        payload += [
            {"role": message["role"], "content": openai_content(message["content"])}
            for message in messages
            if message["role"] != "system"
        ]
        try:
            response = await self.client.chat.completions.create(
                model=model,
                messages=payload,
                max_completion_tokens=max_tokens,
                temperature=temperature,
            )
            choice = response.choices[0]
            return {
                "provider": self.name,
                "model": model,
                "content": choice.message.content or "",
                "finish_reason": choice.finish_reason,
                "usage": {
                    "input_tokens": response.usage.prompt_tokens if response.usage else None,
                    "output_tokens": response.usage.completion_tokens if response.usage else None,
                },
            }
        except Exception as exc:
            raise normalize_provider_exception(exc, provider=self.name) from exc
