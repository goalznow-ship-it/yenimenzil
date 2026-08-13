"""Redis-backed sliding-window rate limiter with in-memory fallback."""

from __future__ import annotations

import logging
import time
import uuid

import redis.asyncio as aioredis

from app.core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


class RateLimiter:
    """Redis-backed sliding-window rate limiter with in-memory fallback."""

    def __init__(
        self,
        prefix: str,
        limit: int,
        window_seconds: int = 60,
        burst_limit: int | None = None,
    ) -> None:
        self.prefix = prefix
        self.limit = limit
        self.window_seconds = window_seconds
        self.burst_limit = burst_limit or limit * 2
        self._redis: aioredis.Redis | None = None
        self._memory: dict[str, list[float]] = {}
        self._memory_lock = False

    async def _get_redis(self) -> aioredis.Redis | None:
        if self._redis is None:
            try:
                self._redis = aioredis.from_url(
                    settings.REDIS_URL,
                    socket_connect_timeout=1,
                    socket_timeout=1,
                    decode_responses=True,
                )
                await self._redis.ping()
            except Exception as exc:  # noqa: BLE001
                logger.debug("Redis unavailable, falling back to memory: %s", exc)
                self._redis = None
        return self._redis

    async def is_allowed(self, key: str) -> bool:
        full_key = f"{self.prefix}:{key}"
        client = await self._get_redis()
        if client is not None:
            try:
                now_ms = int(time.time() * 1000)
                window_start = (time.time() - self.window_seconds) * 1000
                await client.zremrangebyscore(full_key, "-inf", window_start)
                count = await client.zcard(full_key)
                if count >= self.burst_limit:
                    return False
                # Use a unique member to avoid collisions
                member = f"{now_ms}:{uuid.uuid4()}"
                await client.zadd(full_key, {member: now_ms})
                await client.expire(full_key, self.window_seconds * 2)
                return count < self.limit
            except Exception as exc:  # noqa: BLE001
                logger.debug("Rate limiter Redis error, falling back: %s", exc)
        # In-memory fallback so the app still works without Redis.
        now = time.monotonic()
        window = self.window_seconds
        bucket = self._memory.setdefault(full_key, [])
        # Remove outdated entries
        self._memory[full_key] = [ts for ts in bucket if now - ts < window]
        bucket = self._memory[full_key]
        if len(bucket) >= self.burst_limit:
            return False
        # Add current request
        bucket.append(now)
        # Allow if previous count (before adding) was below limit
        return len(bucket) - 1 < self.limit