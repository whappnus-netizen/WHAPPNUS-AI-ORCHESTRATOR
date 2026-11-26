from app.core.provider_errors import normalize_provider_exception

class RateLimitError(Exception):
    status_code = 429
    response = type("Response", (), {"headers": {"retry-after": "7"}})()

class UnauthorizedError(Exception):
    status_code = 401

class InvalidRequestError(Exception):
    status_code = 400

def test_rate_limit_is_retryable_and_retry_after_is_parsed():
    error = normalize_provider_exception(RateLimitError())
    assert error.code == "PROVIDER_RATE_LIMIT"
    assert error.retryable is True
    assert error.retry_after_seconds == 7

def test_auth_error_is_not_retried_but_can_fallback():
    error = normalize_provider_exception(UnauthorizedError())
    assert error.code == "PROVIDER_AUTH_ERROR"
    assert error.retryable is False
    assert error.fallback_allowed is True

def test_invalid_request_does_not_fallback():
    error = normalize_provider_exception(InvalidRequestError())
    assert error.fallback_allowed is False
