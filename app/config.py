from functools import lru_cache
from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")
    app_env: str = "development"
    app_port: int = 8000
    orchestrator_api_key: SecretStr = SecretStr("")
    tenant_signing_secret: SecretStr = SecretStr("")
    redis_url: SecretStr = SecretStr("")
    gemini_api_key: SecretStr = SecretStr("")
    # Gemini 2.5 access is restricted for projects without prior active usage.
    # 3.8 Flash is the current stable default for new Gemini API integrations.
    gemini_flash_model: str = "gemini-3.8-flash"
    gemini_advanced_model: str = "gemini-3.8-flash"
    openai_api_key: SecretStr = SecretStr("")
    openai_model: str = "gpt-4.1-mini"
    anthropic_api_key: SecretStr = SecretStr("")
    anthropic_model: str = "claude-sonnet-4-5"
    default_provider: str = "gemini"
    default_model: str = ""
    enable_fallback: bool = True
    fallback_provider_order: str = "openai,anthropic"
    request_timeout_seconds: float = Field(default=45, gt=0, le=300)
    max_retries: int = Field(default=2, ge=0, le=5)
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
