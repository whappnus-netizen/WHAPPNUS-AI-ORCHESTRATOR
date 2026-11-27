from functools import lru_cache
from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")
    app_env: str = "development"
    app_port: int = 8000
    orchestrator_api_key: SecretStr = SecretStr("")
    tenant_signing_secret: SecretStr = SecretStr("")
    tenant_body_signature_required: bool = False
    redis_url: SecretStr = SecretStr("")
    gemini_api_key: SecretStr = SecretStr("")
    # The primary model is deliberately independent of the legacy GEMINI_FLASH_MODEL variable.
    # This avoids an old production override silently selecting a model with unstable availability.
    gemini_primary_model: str = "gemini-3.1-flash-lite"
    gemini_advanced_model: str = "gemini-3.1-pro-preview"
    gemini_advanced_enabled: bool = False
    openai_api_key: SecretStr = SecretStr("")
    openai_model: str = "gpt-4.1-mini"
    anthropic_api_key: SecretStr = SecretStr("")
    anthropic_model: str = "claude-sonnet-4-5"
    default_provider: str = "gemini"
    default_model: str = ""
    enable_fallback: bool = True
    # Fallback providers are opt-in: add only providers with verified quota/billing.
    fallback_provider_order: str = ""
    request_timeout_seconds: float = Field(default=45, gt=0, le=300)
    total_request_timeout_seconds: float = Field(default=22, gt=0, le=120)
    max_retries: int = Field(default=2, ge=0, le=5)
    max_rate_limit_retries: int = Field(default=1, ge=0, le=2)
    rate_limit_per_minute: int = Field(default=60, ge=1, le=100000)
    rate_limit_window_seconds: int = Field(default=60, ge=1, le=3600)
    max_input_tokens: int = Field(default=100000, ge=1000)
    max_output_tokens: int = Field(default=4096, ge=1)
    model_limits_json: str = "{}"
    model_pricing_json: str = "{}"
    pricing_currency: str = "USD"
    log_level: str = "INFO"

    @property
    def fallback_order(self) -> list[str]:
        return [item.strip().lower() for item in self.fallback_provider_order.split(",") if item.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
