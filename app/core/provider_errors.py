import re

from app.core.errors import ProviderError


_SECRET_PATTERNS = (
    re.compile(r"(?i)bearer\s+[A-Za-z0-9._~+/-]+=*"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{12,}\b"),
    re.compile(r"\bAIza[0-9A-Za-z_-]{20,}\b"),
)


def _safe_message(value) -> str | None:
    if not isinstance(value, str) or not value:
        return None
    message = value[:500]
    for pattern in _SECRET_PATTERNS:
        message = pattern.sub("[redacted]", message)
    return message[:300]


def _error_payload(body):
    if not isinstance(body, dict):
        return {}
    nested = body.get("error", body)
    return nested if isinstance(nested, dict) else {}


def _is_quota_exhausted(provider_code: object, provider_type: object, message: str | None) -> bool:
    code = str(provider_code or "").lower()
    error_type = str(provider_type or "").lower()
    text = (message or "").lower()
    hard_quota_codes = {
        "insufficient_quota",
        "billing_hard_limit_reached",
        "quota_exceeded",
        "insufficient_funds",
    }
    if code in hard_quota_codes:
        return True
    if "credit balance is too low" in text or "insufficient_quota" in text:
        return True
    if "limit: 0" in text and ("quota" in text or "free tier" in text):
        return True
    # RESOURCE_EXHAUSTED can mean a short per-minute limit, not an exhausted plan.
    # Only treat it as a hard quota when the daily quota is exhausted or the limit is zero.
    if code == "resource_exhausted" and "per day" in text and "quota" in text:
        return True
    if "exceeded your current quota" in text and ("per day" in text or "limit: 0" in text):
        return True
    return error_type == "insufficient_quota"


def normalize_provider_exception(exc: Exception, provider: str | None = None) -> ProviderError:
    """Normalize SDK errors while retaining bounded, credential-safe diagnostics."""
    name = type(exc).__name__.lower()
    response = getattr(exc, "response", None)
    headers = getattr(response, "headers", None) or getattr(exc, "headers", None) or {}
    raw_status = getattr(exc, "status_code", None) or getattr(response, "status_code", None) or getattr(exc, "code", None)
    try:
        status = int(raw_status) if raw_status is not None else None
    except (TypeError, ValueError):
        status = None

    status_name = str(getattr(exc, "status", "") or "").upper()
    if status is None and status_name in {"NOT_FOUND", "NOTFOUND"}:
        status = 404
    elif status is None and status_name in {"RESOURCE_EXHAUSTED", "TOO_MANY_REQUESTS"}:
        status = 429
    elif status is None and status_name in {"UNAVAILABLE", "INTERNAL"}:
        status = 503

    body = _error_payload(getattr(exc, "body", None))
    provider_code = body.get("code") or body.get("status")
    provider_type = body.get("type") or name
    provider_message = _safe_message(body.get("message") or getattr(exc, "message", None) or str(exc))
    request_id = (
        getattr(exc, "request_id", None)
        or headers.get("request-id")
        or headers.get("x-request-id")
        or headers.get("x-goog-request-id")
    )
    request_id = str(request_id)[:128] if request_id else None

    retry_after = None
    try:
        raw_retry = headers.get("retry-after")
        if raw_retry is not None:
            retry_after = min(30.0, max(0.0, float(raw_retry)))
        else:
            details = body.get("details", [])
            if isinstance(details, list):
                for detail in details:
                    if not isinstance(detail, dict) or not str(detail.get("@type", "")).endswith("RetryInfo"):
                        continue
                    match = re.fullmatch(r"\\s*(\\d+(?:\\.\\d+)?)s\\s*", str(detail.get("retryDelay", "")))
                    if match:
                        retry_after = min(30.0, max(0.0, float(match.group(1))))
                        break
    except (TypeError, ValueError, AttributeError):
        retry_after = None

    common = {
        "provider": provider,
        "provider_error_code": str(provider_code)[:100] if provider_code is not None else None,
        "provider_error_type": str(provider_type)[:100] if provider_type is not None else None,
        "provider_request_id": request_id,
        "provider_message": provider_message,
    }

    if _is_quota_exhausted(provider_code, provider_type, provider_message):
        return ProviderError(
            "PROVIDER_QUOTA_EXHAUSTED",
            "Provider quota or billing balance is exhausted for this model/account.",
            False,
            status,
            None,
            True,
            **common,
        )
    if "ratelimit" in name or status == 429:
        return ProviderError("PROVIDER_RATE_LIMIT", "Provider rate limit reached.", True, status, retry_after, True, **common)
    if "authentication" in name or "permission" in name or status in (401, 403):
        return ProviderError("PROVIDER_AUTH_ERROR", "Provider authentication or permission failed.", False, status, fallback_allowed=True, **common)
    if status == 404 or "notfound" in name or status_name in {"NOT_FOUND", "NOTFOUND"}:
        return ProviderError("PROVIDER_MODEL_NOT_FOUND", "Provider model or endpoint was not found.", False, status or 404, fallback_allowed=True, **common)
    if "badrequest" in name or "invalid" in name or status in (400, 413, 422):
        code = "CONTEXT_TOO_LARGE" if status == 413 else "PROVIDER_REQUEST_INVALID"
        return ProviderError(code, "Provider rejected this provider-specific request.", False, status, fallback_allowed=True, **common)
    if "timeout" in name or "connection" in name or status == 408 or (status is not None and status >= 500):
        return ProviderError("PROVIDER_TRANSIENT_ERROR", "Provider temporarily unavailable.", True, status, retry_after, True, **common)
    return ProviderError("PROVIDER_ERROR", "Provider request failed.", False, status, fallback_allowed=True, **common)
