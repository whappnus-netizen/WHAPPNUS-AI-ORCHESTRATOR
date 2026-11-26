import hashlib
import hmac
import time

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.main import app
from app.security.tenant_auth import verify_tenant_signature


def test_provider_endpoint_requires_auth():
    response = TestClient(app).get("/v1/providers")
    assert response.status_code in (401, 503)


def _signature(org, timestamp, nonce, secret):
    message = f"{org}:{timestamp}:{nonce}".encode()
    return hmac.new(secret.encode(), message, hashlib.sha256).hexdigest()


def test_valid_tenant_signature_is_accepted():
    org, nonce, secret = "org-test", "random-nonce-at-least-16", "tenant-secret-for-tests-only"
    timestamp = str(int(time.time()))
    verify_tenant_signature(
        organization_id=org,
        timestamp=timestamp,
        nonce=nonce,
        signature=_signature(org, timestamp, nonce, secret),
        secret=secret,
    )


def test_invalid_tenant_signature_is_rejected():
    with pytest.raises(HTTPException) as error:
        verify_tenant_signature(
            organization_id="org-test",
            timestamp=str(int(time.time())),
            nonce="random-nonce-at-least-16",
            signature="0" * 64,
            secret="tenant-secret-for-tests-only",
        )
    assert error.value.status_code == 401


def test_expired_tenant_signature_is_rejected():
    timestamp = str(int(time.time()) - 600)
    with pytest.raises(HTTPException) as error:
        verify_tenant_signature(
            organization_id="org-test",
            timestamp=timestamp,
            nonce="random-nonce-at-least-16",
            signature=_signature(
                "org-test", timestamp, "random-nonce-at-least-16", "tenant-secret-for-tests-only"
            ),
            secret="tenant-secret-for-tests-only",
        )
    assert error.value.status_code == 401
