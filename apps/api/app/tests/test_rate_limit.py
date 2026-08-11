import uuid

import pytest

from app.core.rate_limit import RateLimiter


def _prefix() -> str:
    return f"rl:test:{uuid.uuid4().hex}"


@pytest.mark.asyncio
async def test_rate_limiter_allows_up_to_limit_then_blocks():
    limiter = RateLimiter(_prefix(), limit=3, window_seconds=60, burst_limit=5)
    allowed = [await limiter.is_allowed("ip-1") for _ in range(5)]
    assert allowed == [True, True, True, False, False]


@pytest.mark.asyncio
async def test_rate_limiter_isolates_keys():
    limiter = RateLimiter(_prefix(), limit=2, window_seconds=60)
    await limiter.is_allowed("ip-a")
    await limiter.is_allowed("ip-a")
    assert await limiter.is_allowed("ip-a") is False
    assert await limiter.is_allowed("ip-b") is True


@pytest.mark.asyncio
async def test_rate_limiter_window_expires():
    limiter = RateLimiter(_prefix(), limit=1, window_seconds=0)
    assert await limiter.is_allowed("ip-1") is True
    assert await limiter.is_allowed("ip-1") is True
