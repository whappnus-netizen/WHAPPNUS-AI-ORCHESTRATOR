from app.config import Settings

def test_providers_can_start_without_credentials():
    settings = Settings(_env_file=None)
    assert settings.gemini_api_key.get_secret_value() == ''
    assert settings.openai_api_key.get_secret_value() == ''
    assert settings.anthropic_api_key.get_secret_value() == ''
