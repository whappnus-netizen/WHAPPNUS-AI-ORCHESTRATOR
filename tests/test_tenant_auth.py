import hashlib
import hmac
import time
import pytest
from fastapi import HTTPException
from app.security.tenant_auth import verify_tenant_signature

def test_valid_tenant_signature():
    secret = "test-secret"
    timestamp = str(int(time.time()))
    signature = hmac.new(secret.encode(), f"org-1:{timestamp}".encode(), hashlib.sha256).hexdigest()
    verify_tenant_signature(organization_id="org-1", timestamp=timestamp, signature=signature, secret=secret)

def test_tenant_signature_cannot_be_replayed_for_another_org():
    secret = "test-secret"
    timestamp = str(int(time.time()))
    signature = hmac.new(secret.encode(), f"org-1:{timestamp}".encode(), hashlib.sha256).hexdigest()
    with pytest.raises(HTTPException):
        verify_tenant_signature(organization_id="org-2", timestamp=timestamp, signature=signature, secret=secret)

def test_expired_tenant_signature_is_rejected():
    with pytest.raises(HTTPException):
        verify_tenant_signature(organization_id="org-1", timestamp="1", signature="x", secret="test-secret")
