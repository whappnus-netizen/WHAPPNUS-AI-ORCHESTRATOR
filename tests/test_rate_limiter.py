import pytest
from fastapi import HTTPException

from app.security.rate_limiter import OrganizationRateLimiter


@pytest.mark.asyncio
async def test_development_limiter_is_scoped_per_organization():
    limiter = OrganizationRateLimiter("", 1, 60, "development")
    await limiter.enforce("org-a")
    await limiter.enforce("org-b")
    with pytest.raises(HTTPException) as error:
        await limiter.enforce("org-a")
    assert error.value.status_code == 429
    assert error.value.headers["Retry-After"]


@pytest.mark.asyncio
async def test_production_requires_shared_redis():
    limiter = OrganizationRateLimiter("", 5, 60, "production")
    with pytest.raises(HTTPException) as error:
        await limiter.enforce("org-a")
    assert error.value.status_code == 503
    assert await limiter.health_check() is False


@pytest.mark.asyncio
async def test_development_can_use_local_limiter_without_redis():
    limiter = OrganizationRateLimiter("", 5, 60, "development")
    assert await limiter.health_check() is True
