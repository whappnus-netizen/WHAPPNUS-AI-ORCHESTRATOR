import pytest
from fastapi import HTTPException
from app.security.rate_limiter import OrganizationRateLimiter

@pytest.mark.asyncio
async def test_development_nonce_can_only_be_consumed_once():
    limiter = OrganizationRateLimiter("", 10, 60, "development")
    await limiter.consume_nonce("org-a", "a-random-nonce-value-12345")
    with pytest.raises(HTTPException) as error:
        await limiter.consume_nonce("org-a", "a-random-nonce-value-12345")
    assert error.value.status_code == 401
    assert error.value.detail["code"] == "TENANT_REQUEST_REPLAYED"
