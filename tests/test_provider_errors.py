from app.core.provider_errors import normalize_provider_exception


class RateLimitError(Exception):
    status_code = 429
    response = type("Response", (), {"headers": {"retry-after": "7"}})()


class UnauthorizedError(Exception):
    status_code = 401


class InvalidRequestError(Exception):
    status_code = 400
    body = {"error": {"type": "invalid_request_error", "code": "invalid_parameter", "message": "Unsupported parameter"}}


class ModelNotFoundError(Exception):
    status_code = 404
    request_id = "provider-request-123"
    body = {"error": {"type": "not_found_error", "code": "model_not_found", "message": "Model was not found"}}


def test_rate_limit_is_retryable_and_retry_after_is_parsed():
    error = normalize_provider_exception(RateLimitError(), provider="openai")
    assert error.code == "PROVIDER_RATE_LIMIT"
    assert error.retryable is True
    assert error.retry_after_seconds == 7
    assert error.provider == "openai"


def test_auth_error_is_not_retried_but_can_fallback():
    error = normalize_provider_exception(UnauthorizedError(), provider="anthropic")
    assert error.code == "PROVIDER_AUTH_ERROR"
    assert error.retryable is False
    assert error.fallback_allowed is True


def test_provider_specific_invalid_request_can_fallback_without_retry():
    error = normalize_provider_exception(InvalidRequestError(), provider="anthropic")
    assert error.code == "PROVIDER_REQUEST_INVALID"
    assert error.retryable is False
    assert error.fallback_allowed is True
    assert error.provider_error_code == "invalid_parameter"
    assert error.provider_message == "Unsupported parameter"


def test_model_not_found_is_not_retried_but_allows_fallback():
    error = normalize_provider_exception(ModelNotFoundError(), provider="gemini")
    assert error.code == "PROVIDER_MODEL_NOT_FOUND"
    assert error.retryable is False
    assert error.fallback_allowed is True
    assert error.provider_request_id == "provider-request-123"
