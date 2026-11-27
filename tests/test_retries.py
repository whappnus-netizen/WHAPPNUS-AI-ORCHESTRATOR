import asyncio

import pytest

from app.utils.retries import backoff


@pytest.mark.asyncio
async def test_backoff_never_exceeds_remaining_global_deadline(monkeypatch):
    observed = []

    async def fake_sleep(delay):
        observed.append(delay)

    monkeypatch.setattr(asyncio, "sleep", fake_sleep)
    await backoff(attempt=0, retry_after=30, max_wait_seconds=0.02)

    assert len(observed) == 1
    assert observed[0] <= 0.02
