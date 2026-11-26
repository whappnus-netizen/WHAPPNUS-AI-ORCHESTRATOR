import asyncio
import hashlib
import time
from collections import defaultdict, deque
from fastapi import HTTPException

class OrganizationRateLimiter:
    """Atomic Redis fixed-window limiter; process-local fallback is development-only."""
    _SCRIPT = """
    local current = redis.call('INCR', KEYS[1])
    if current == 1 then redis.call('EXPIRE', KEYS[1], ARGV[1]) end
    local ttl = redis.call('TTL', KEYS[1])
    return {current, ttl}
    """
    def __init__(self, redis_url: str, limit: int, window_seconds: int, environment: str):
        self.redis_url, self.limit, self.window_seconds, self.environment = redis_url, limit, window_seconds, environment
        self._redis = None
        self._local = defaultdict(deque)
        self._lock = asyncio.Lock()

    async def check(self, organization_id: str) -> tuple[int, int]:
        digest = hashlib.sha256(organization_id.encode()).hexdigest()
        if self.redis_url:
            if self._redis is None:
                from redis.asyncio import Redis
                self._redis = Redis.from_url(self.redis_url, decode_responses=True, socket_connect_timeout=3, socket_timeout=3)
            key = f"whappnus:orchestrator:rate:{digest}"
            try:
                count, ttl = await self._redis.eval(self._SCRIPT, 1, key, self.window_seconds)
            except Exception as exc:
                raise HTTPException(status_code=503, detail={"code": "RATE_LIMIT_STORE_UNAVAILABLE"}) from exc
            return int(count), max(1, int(ttl))
        if self.environment.lower() in {"production", "prod"}:
            raise HTTPException(status_code=503, detail={"code": "DISTRIBUTED_RATE_LIMIT_NOT_CONFIGURED"})
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
            raise HTTPException(status_code=429, headers={"Retry-After": str(retry_after)}, detail={"code": "ORGANIZATION_RATE_LIMIT_EXCEEDED", "retry_after": retry_after})
