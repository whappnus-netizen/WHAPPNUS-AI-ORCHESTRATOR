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


def signed_v2(secret, organization_id, timestamp, nonce, body_hash):
    message = f"POST:/v1/chat/completions:{organization_id}:{timestamp}:{nonce}:{body_hash}"
    return hmac.new(secret.encode(), message.encode(), hashlib.sha256).hexdigest()


def test_valid_v2_signature_binds_method_path_tenant_and_body_hash():
    secret = "test-secret"
    timestamp = str(int(time.time()))
    nonce = "nonce-value-long-enough"
    body_hash = hashlib.sha256(b'{"organization_id":"org-1"}').hexdigest()
    verify_tenant_signature(
        organization_id="org-1",
        timestamp=timestamp,
        nonce=nonce,
        signature=signed_v2(secret, "org-1", timestamp, nonce, body_hash),
        secret=secret,
        body_hash=body_hash,
        method="POST",
        path="/v1/chat/completions",
    )


def test_v2_signature_rejects_tampered_body_hash():
    secret = "test-secret"
    timestamp = str(int(time.time()))
    nonce = "nonce-value-long-enough"
    original_hash = hashlib.sha256(b'{"organization_id":"org-1"}').hexdigest()
    tampered_hash = hashlib.sha256(b'{"organization_id":"org-2"}').hexdigest()
    with pytest.raises(HTTPException):
        verify_tenant_signature(
            organization_id="org-1",
            timestamp=timestamp,
            nonce=nonce,
            signature=signed_v2(secret, "org-1", timestamp, nonce, original_hash),
            secret=secret,
            body_hash=tampered_hash,
            method="POST",
            path="/v1/chat/completions",
        )


def test_body_hash_verification_accepts_exact_raw_body():
    from app.security.tenant_auth import verify_tenant_body_hash

    raw = b'{"organization_id":"org-1"}'
    expected = hashlib.sha256(raw).hexdigest()
    assert verify_tenant_body_hash(raw_body=raw, body_hash=expected, required=True) == expected


def test_body_hash_verification_rejects_tampered_raw_body():
    from app.security.tenant_auth import verify_tenant_body_hash

    original = b'{"organization_id":"org-1"}'
    tampered = b'{"organization_id":"org-2"}'
    expected = hashlib.sha256(original).hexdigest()
    with pytest.raises(HTTPException):
        verify_tenant_body_hash(raw_body=tampered, body_hash=expected, required=True)


def test_required_body_hash_rejects_legacy_request():
    from app.security.tenant_auth import verify_tenant_body_hash

    with pytest.raises(HTTPException):
        verify_tenant_body_hash(raw_body=b"{}", body_hash=None, required=True)


def test_body_hash_is_optional_during_compatibility_rollout():
    from app.security.tenant_auth import verify_tenant_body_hash

    assert verify_tenant_body_hash(raw_body=b"{}", body_hash=None, required=False) is None
