import hashlib
import hmac
import re
import time

from fastapi import HTTPException


def verify_tenant_body_hash(*, raw_body: bytes, body_hash: str | None, required: bool = False) -> str | None:
    if not body_hash:
        if required:
            raise HTTPException(status_code=401, detail={"code": "TENANT_BODY_HASH_REQUIRED"})
        return None
    if not re.fullmatch(r"[0-9a-fA-F]{64}", body_hash):
        raise HTTPException(status_code=401, detail={"code": "TENANT_BODY_HASH_INVALID"})
    actual = hashlib.sha256(raw_body).hexdigest()
    normalized = body_hash.lower()
    if not hmac.compare_digest(normalized, actual):
        raise HTTPException(status_code=401, detail={"code": "TENANT_BODY_HASH_MISMATCH"})
    return normalized


def verify_tenant_signature(
    *,
    organization_id: str,
    timestamp: str | None,
    nonce: str | None,
    signature: str | None,
    secret: str,
    body_hash: str | None = None,
    method: str = "POST",
    path: str = "/v1/chat/completions",
    max_skew_seconds: int = 300,
) -> None:
    if not secret:
        raise HTTPException(status_code=503, detail={"code": "TENANT_AUTH_NOT_CONFIGURED"})
    if not timestamp or not nonce or not signature or len(nonce) < 16 or len(nonce) > 128:
        raise HTTPException(status_code=401, detail={"code": "TENANT_SIGNATURE_REQUIRED"})
    try:
        issued_at = int(timestamp)
    except (TypeError, ValueError):
        raise HTTPException(status_code=401, detail={"code": "TENANT_SIGNATURE_INVALID"}) from None
    if abs(int(time.time()) - issued_at) > max_skew_seconds:
        raise HTTPException(status_code=401, detail={"code": "TENANT_SIGNATURE_EXPIRED"})
    if body_hash:
        message = f"{method.upper()}:{path}:{organization_id}:{issued_at}:{nonce}:{body_hash}".encode()
    else:
        # Legacy v1 remains temporarily accepted while backend and Orchestrator
        # are rolled out in order. Set TENANT_BODY_SIGNATURE_REQUIRED=true
        # after all callers have moved to v2.
        message = f"{organization_id}:{issued_at}:{nonce}".encode()
    expected = hmac.new(secret.encode(), message, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(signature, expected):
        raise HTTPException(status_code=401, detail={"code": "TENANT_SIGNATURE_INVALID"})
