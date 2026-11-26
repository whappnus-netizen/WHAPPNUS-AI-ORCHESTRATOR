import asyncio
import random

async def backoff(attempt: int, base_seconds: float = 0.5, cap_seconds: float = 8.0, retry_after: float | None = None) -> None:
    exponential = min(cap_seconds, base_seconds * (2 ** max(0, attempt)))
    jittered = random.uniform(exponential * 0.5, exponential)
    delay = max(jittered, min(cap_seconds, retry_after or 0.0))
    await asyncio.sleep(min(cap_seconds, delay))
