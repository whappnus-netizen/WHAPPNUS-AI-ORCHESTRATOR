from app.core.errors import ProviderError

def normalize_provider_exception(exc: Exception) -> ProviderError:
    """Normalize SDK errors without leaking provider messages or credentials."""
    name = type(exc).__name__.lower()
    status = getattr(exc, "status_code", None) or getattr(exc, "code", None)
    response = getattr(exc, "response", None)
    headers = getattr(response, "headers", None) or getattr(exc, "headers", None) or {}
    retry_after = None
    try:
        status = int(status) if status is not None else None
    except (TypeError, ValueError):
        status = None
    try:
        raw_retry = headers.get("retry-after")
        retry_after = min(30.0, max(0.0, float(raw_retry))) if raw_retry is not None else None
    except (TypeError, ValueError, AttributeError):
        retry_after = None
    if "authentication" in name or "permission" in name or status in (401, 403):
        return ProviderError("PROVIDER_AUTH_ERROR", "Provider authentication or permission failed.", False, status)
    if "badrequest" in name or "invalid" in name or status in (400, 404, 413, 422):
        code = "CONTEXT_TOO_LARGE" if status == 413 else "PROVIDER_REQUEST_INVALID"
        return ProviderError(code, "Provider rejected the request.", False, status, fallback_allowed=False)
    if "ratelimit" in name or status == 429:
        return ProviderError("PROVIDER_RATE_LIMIT", "Provider rate limit reached.", True, status, retry_after)
    if "timeout" in name or "connection" in name or status == 408 or (status is not None and status >= 500):
        return ProviderError("PROVIDER_TRANSIENT_ERROR", "Provider temporarily unavailable.", True, status, retry_after)
    return ProviderError("PROVIDER_ERROR", "Provider request failed.", False, status)
