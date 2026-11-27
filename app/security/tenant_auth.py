import hashlib
import hmac
import time
from fastapi import HTTPException

def verify_tenant_signature(*, organization_id: str, timestamp: str | None, nonce: str | None, signature: str | None, secret: str, max_skew_seconds: int = 300) -> None:
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
    message = f"{organization_id}:{issued_at}:{nonce}".encode()
    expected = hmac.new(secret.encode(), message, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(signature, expected):
        raise HTTPException(status_code=401, detail={"code": "TENANT_SIGNATURE_INVALID"})
