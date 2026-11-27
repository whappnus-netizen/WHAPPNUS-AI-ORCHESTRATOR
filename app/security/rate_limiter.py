import asyncio
import hashlib
import time
from collections import defaultdict, deque

from fastapi import HTTPException


class OrganizationRateLimiter:
    """Atomic Redis quotas and one-time tenant nonces; local fallback is development-only."""

    _SCRIPT = """
    local current = redis.call('INCR', KEYS[1])
    if current == 1 then redis.call('EXPIRE', KEYS[1], ARGV[1]) end
    local ttl = redis.call('TTL', KEYS[1])
    return {current, ttl}
    """

    def __init__(self, redis_url: str, limit: int, window_seconds: int, environment: str):
        self.redis_url = redis_url
        self.limit = limit
        self.window_seconds = window_seconds
        self.environment = environment
        self._redis = None
        self._local = defaultdict(deque)
        self._nonces = {}
        self._lock = asyncio.Lock()

    async def _client(self):
        if self._redis is None:
            from redis.asyncio import Redis
            self._redis = Redis.from_url(
                self.redis_url,
                decode_responses=True,
                socket_connect_timeout=3,
                socket_timeout=3,
            )
        return self._redis

    async def health_check(self) -> bool:
        if not self.redis_url:
            return self.environment.lower() not in {"production", "prod"}
        try:
            return bool(await (await self._client()).ping())
        except Exception:
            return False

    async def consume_nonce(self, organization_id: str, nonce: str) -> None:
        digest = hashlib.sha256(organization_id.encode()).hexdigest()
        if self.redis_url:
            try:
                accepted = await (await self._client()).set(
                    f"whappnus:orchestrator:nonce:{digest}:{nonce}",
                    "1",
                    ex=300,
                    nx=True,
                )
            except Exception as exc:
                raise HTTPException(
                    status_code=503,
                    detail={"code": "TENANT_REPLAY_STORE_UNAVAILABLE"},
                ) from exc
            if not accepted:
                raise HTTPException(status_code=401, detail={"code": "TENANT_REQUEST_REPLAYED"})
            return

        if self.environment.lower() in {"production", "prod"}:
            raise HTTPException(
                status_code=503,
                detail={"code": "DISTRIBUTED_REPLAY_PROTECTION_NOT_CONFIGURED"},
            )
        now = time.monotonic()
        async with self._lock:
            self._nonces = {key: expiry for key, expiry in self._nonces.items() if expiry > now}
            key = f"{digest}:{nonce}"
            if key in self._nonces:
                raise HTTPException(status_code=401, detail={"code": "TENANT_REQUEST_REPLAYED"})
            self._nonces[key] = now + 300

    async def check(self, organization_id: str) -> tuple[int, int]:
        digest = hashlib.sha256(organization_id.encode()).hexdigest()
        if self.redis_url:
            try:
                count, ttl = await (await self._client()).eval(
                    self._SCRIPT,
                    1,
                    f"whappnus:orchestrator:rate:{digest}",
                    self.window_seconds,
                )
            except Exception as exc:
                raise HTTPException(
                    status_code=503,
                    detail={"code": "RATE_LIMIT_STORE_UNAVAILABLE"},
                ) from exc
            return int(count), max(1, int(ttl))

        if self.environment.lower() in {"production", "prod"}:
            raise HTTPException(
                status_code=503,
                detail={"code": "DISTRIBUTED_RATE_LIMIT_NOT_CONFIGURED"},
            )
        now = time.monotonic()
        async with self._lock:
            bucket = self._local[digest]
            while bucket and now - bucket[0] >= self.window_seconds:
                bucket.popleft()
            bucket.append(now)
            return len(bucket), max(1, self.window_seconds - int(now - bucket[0]))

    async def enforce(self, organization_id: str) -> None:
        count, retry_after = await self.check(organization_id)
        if count > self.limit:
            raise HTTPException(
                status_code=429,
                headers={"Retry-After": str(retry_after)},
                detail={
                    "code": "ORGANIZATION_RATE_LIMIT_EXCEEDED",
                    "retry_after": retry_after,
                },
            )
