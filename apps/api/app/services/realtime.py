"""Redis pub/sub bridge for real-time user events (SSE transport).

Events are published best-effort: if Redis is unavailable the publish is
skipped and clients fall back to polling. Channels are per-user so the
message bus never fans out globally.
"""

from __future__ import annotations

import asyncio
import json
import logging

import redis.asyncio as aioredis

from app.core.config import get_settings

logger = logging.getLogger(__name__)

HEARTBEAT_INTERVAL_SECONDS = 15

_redis_client: aioredis.Redis | None = None


def _channel(user_id) -> str:
    return f"realtime:user:{user_id}"


async def _client() -> aioredis.Redis | None:
    global _redis_client
    if _redis_client is None:
        try:
            settings = get_settings()
            _redis_client = aioredis.from_url(
                settings.REDIS_URL,
                socket_connect_timeout=1,
                socket_timeout=1,
                decode_responses=True,
            )
            await _redis_client.ping()
        except Exception as exc:  # noqa: BLE001
            logger.debug("Redis unavailable for realtime events: %s", exc)
            _redis_client = None
    return _redis_client


async def publish_user_event(user_id, event: dict) -> None:
    """Best-effort publish of a JSON event to a user's channel."""
    try:
        client = await _client()
        if client is None:
            return
        await client.publish(_channel(user_id), json.dumps(event, default=str))
    except Exception as exc:  # noqa: BLE001
        logger.debug("Failed to publish realtime event: %s", exc)


async def user_event_stream(user_id):
    """Async generator of (channel, payload) tuples for a user's events.

    Yields (None, None) heartbeats every 15 seconds so proxies do not drop
    the connection. The caller is responsible for unsubscribing.
    """
    client = await _client()
    if client is None:
        while True:
            await asyncio.sleep(HEARTBEAT_INTERVAL_SECONDS)
            yield None, None

    pubsub = client.pubsub()
    await pubsub.subscribe(_channel(user_id))
    try:
        while True:
            message = await pubsub.get_message(
                ignore_subscribe_messages=True, timeout=HEARTBEAT_INTERVAL_SECONDS
            )
            if message is None:
                yield None, None
                continue
            payload = message.get("data")
            if isinstance(payload, str):
                yield message.get("channel"), payload
    finally:
        await pubsub.unsubscribe(_channel(user_id))
        await pubsub.close()
