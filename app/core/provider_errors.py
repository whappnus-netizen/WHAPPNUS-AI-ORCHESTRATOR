from app.core.errors import ProviderError


def normalize_provider_exception(exc: Exception) -> ProviderError:
    """Conservative cross-SDK error mapping; only transient failures are retryable."""
    name = type(exc).__name__.lower()
    status = getattr(exc, 'status_code', None) or getattr(exc, 'code', None)
    try:
        status = int(status) if status is not None else None
    except (TypeError, ValueError):
        status = None
    if 'authentication' in name or 'permission' in name or status in (401, 403):
        return ProviderError('PROVIDER_AUTH_ERROR', 'Provider authentication or permission failed.', False, status)
    if 'badrequest' in name or 'invalid' in name or status in (400, 404, 413, 422):
        code = 'CONTEXT_TOO_LARGE' if status == 413 else 'PROVIDER_REQUEST_INVALID'
        return ProviderError(code, 'Provider rejected the request.', False, status)
    if 'ratelimit' in name or status == 429:
        return ProviderError('PROVIDER_RATE_LIMIT', 'Provider rate limit reached.', True, status)
    if 'timeout' in name or 'connection' in name or status == 408 or (status is not None and status >= 500):
        return ProviderError('PROVIDER_TRANSIENT_ERROR', 'Provider temporarily unavailable.', True, status)
    return ProviderError('PROVIDER_ERROR', 'Provider request failed.', False, status)
