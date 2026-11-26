import asyncio
import random

async def backoff(attempt: int, base_seconds: float = 0.5, cap_seconds: float = 8.0) -> None:
    delay=min(cap_seconds, base_seconds * (2 ** max(0, attempt)))
    await asyncio.sleep(random.uniform(delay * 0.5, delay))
