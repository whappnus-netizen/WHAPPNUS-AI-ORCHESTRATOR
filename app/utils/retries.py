import asyncio
import random


async def backoff(
    attempt: int,
    base_seconds: float = 0.5,
    cap_seconds: float = 8.0,
    retry_after: float | None = None,
    max_wait_seconds: float | None = None,
) -> None:
    exponential = min(cap_seconds, base_seconds * (2 ** max(0, attempt)))
    jittered = random.uniform(exponential * 0.5, exponential)
    # Retry-After is already bounded by provider_errors.py (maximum 30 seconds).
    # Do not clamp a provider-requested wait to the shorter exponential backoff cap.
    requested = min(30.0, max(0.0, retry_after or 0.0))
    delay = max(jittered, requested)
    if max_wait_seconds is not None:
        delay = min(delay, max(0.0, max_wait_seconds))
    if delay > 0:
        await asyncio.sleep(delay)
