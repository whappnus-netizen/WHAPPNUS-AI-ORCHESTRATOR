from app.core.errors import ProviderError
from app.core.provider_errors import normalize_provider_exception
from app.providers.base import BaseProvider
from app.providers.multimodal import gemini_content


class GeminiProvider(BaseProvider):
    name = "gemini"

    def __init__(self, settings):
        self.settings = settings
        self.is_configured = bool(settings.gemini_api_key.get_secret_value())
        self.client = None
        if self.is_configured:
            from google import genai
            self.client = genai.Client(api_key=settings.gemini_api_key.get_secret_value())

    def validate_configuration(self):
        return self.is_configured

    def get_capabilities(self):
        models = [self.settings.gemini_flash_model, self.settings.gemini_advanced_model]
        if self.settings.default_provider == self.name and self.settings.default_model:
            models.append(self.settings.default_model)
        return {
            "provider": self.name,
            "models": list(dict.fromkeys(models)),
            "capabilities": ["text", "image", "audio", "document"],
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
            raise ProviderError("PROVIDER_UNAVAILABLE", "Gemini credentials are not configured.")
        from google.genai import types
        try:
            config = types.GenerateContentConfig(
                system_instruction=system,
                max_output_tokens=max_tokens,
                temperature=temperature,
            )
            response = await self.client.aio.models.generate_content(
                model=model,
                contents=gemini_content(messages, system),
                config=config,
            )
            usage = getattr(response, "usage_metadata", None)
            return {
                "provider": self.name,
                "model": model,
                "content": response.text or "",
                "finish_reason": "stop",
                "usage": {
                    "input_tokens": getattr(usage, "prompt_token_count", None),
                    "output_tokens": getattr(usage, "candidates_token_count", None),
                },
            }
        except Exception as exc:
            raise normalize_provider_exception(exc, provider=self.name) from exc
