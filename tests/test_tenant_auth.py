import hashlib
import hmac
import time
import pytest
from fastapi import HTTPException
from app.security.tenant_auth import verify_tenant_signature

def signed(secret, organization_id, timestamp, nonce):
    return hmac.new(secret.encode(), f"{organization_id}:{timestamp}:{nonce}".encode(), hashlib.sha256).hexdigest()

def test_valid_tenant_signature():
    secret, timestamp, nonce = "test-secret", str(int(time.time())), "nonce-value-long-enough"
    verify_tenant_signature(organization_id="org-1", timestamp=timestamp, nonce=nonce, signature=signed(secret, "org-1", timestamp, nonce), secret=secret)

def test_tenant_signature_cannot_be_reused_for_another_org():
    secret, timestamp, nonce = "test-secret", str(int(time.time())), "nonce-value-long-enough"
    with pytest.raises(HTTPException):
        verify_tenant_signature(organization_id="org-2", timestamp=timestamp, nonce=nonce, signature=signed(secret, "org-1", timestamp, nonce), secret=secret)

def test_expired_tenant_signature_is_rejected():
    with pytest.raises(HTTPException):
        verify_tenant_signature(organization_id="org-1", timestamp="1", nonce="nonce-value-long-enough", signature="x", secret="test-secret")

def test_missing_nonce_is_rejected():
    with pytest.raises(HTTPException):
        verify_tenant_signature(organization_id="org-1", timestamp=str(int(time.time())), nonce=None, signature="x", secret="test-secret")
