"""Phase 14: real-time messaging (SSE stream, pub/sub events, read receipts)."""

from __future__ import annotations

import asyncio
import json

import pytest

from app.services import realtime


@pytest.mark.asyncio
async def test_stream_requires_auth(client):
    response = await client.get("/api/v1/conversations/stream")
    assert response.status_code == 401


class _FakeRedisClient:
    """Minimal stub: records publishes, returns a stub pubsub."""

    def __init__(self) -> None:
        self.published: list[tuple[str, str]] = []
        self.pubsub_ = _FakePubSub(self)

    async def publish(self, channel: str, payload: str) -> int:
        self.published.append((channel, payload))
        await self.pubsub_._queue.put({"channel": channel, "data": payload})
        return 1

    def pubsub(self) -> _FakePubSub:
        return self.pubsub_


class _FakePubSub:
    def __init__(self, client: _FakeRedisClient) -> None:
        self.client = client
        self.subscribed: list[str] = []
        self.unsubscribed: list[str] = []
        self.closed = False
        self._queue: asyncio.Queue = asyncio.Queue()

    async def subscribe(self, *channels: str) -> None:
        self.subscribed.extend(channels)

    async def unsubscribe(self, *channels: str) -> None:
        self.unsubscribed.extend(channels)

    async def close(self) -> None:
        self.closed = True

    async def get_message(self, ignore_subscribe_messages=True, timeout=None):
        try:
            return await asyncio.wait_for(self._queue.get(), timeout=timeout or 0.2)
        except TimeoutError:
            return None


@pytest.mark.asyncio
async def test_publish_and_receive_event(monkeypatch):
    monkeypatch.setattr(realtime, "HEARTBEAT_INTERVAL_SECONDS", 0.05)
    fake = _FakeRedisClient()
    monkeypatch.setattr(realtime, "_client", _fake_client_loader(fake))

    await realtime.publish_user_event(
        "user-1", {"type": "message", "conversation_id": "c1"}
    )
    assert fake.published == [
        (
            "realtime:user:user-1",
            json.dumps({"type": "message", "conversation_id": "c1"}),
        )
    ]

    stream = realtime.user_event_stream("user-1")
    payload = await asyncio.wait_for(anext(stream), timeout=1)
    assert payload == (
        "realtime:user:user-1",
        json.dumps({"type": "message", "conversation_id": "c1"}),
    )
    # Heartbeat follows once the queue is drained
    heartbeat = await asyncio.wait_for(anext(stream), timeout=1)
    assert heartbeat == (None, None)
    await stream.aclose()
    assert fake.pubsub_.unsubscribed == ["realtime:user:user-1"]
    assert fake.pubsub_.closed


def _fake_client_loader(fake: _FakeRedisClient):
    async def loader():
        return fake

    return loader


@pytest.mark.asyncio
async def test_stream_degrades_to_heartbeat_without_redis(monkeypatch):
    async def no_client():
        return None

    monkeypatch.setattr(realtime, "HEARTBEAT_INTERVAL_SECONDS", 0.01)
    monkeypatch.setattr(realtime, "_client", no_client)
    stream = realtime.user_event_stream("user-x")
    first = await asyncio.wait_for(anext(stream), timeout=1)
    assert first == (None, None)
    await stream.aclose()


@pytest.mark.asyncio
async def test_send_message_publishes_realtime_event(
    client, auth_user, feature_catalog, db, monkeypatch
):
    from app.tests.test_phase7_marketplace import _create_active_property

    owner = await auth_user(email="owner-realtime@test.az", is_verified=True)
    buyer = await auth_user(email="buyer-realtime@test.az")
    prop = await _create_active_property(db, owner)

    calls: list[tuple] = []

    async def spy(user_id, event):
        calls.append((user_id, event))

    monkeypatch.setattr("app.api.v1.endpoints.messaging.publish_user_event", spy)

    response = await client.post(
        "/api/v1/conversations",
        json={"property_id": str(prop.id), "message": "Salam"},
    )
    assert response.status_code == 201
    conv_id = response.json()["id"]

    assert len(calls) == 2
    assert all(c[1]["type"] == "conversation" for c in calls)
    assert all(c[1]["conversation_id"] == conv_id for c in calls)
    assert {str(c[0]) for c in calls} == {str(owner.id), str(buyer.id)}

    calls.clear()
    response = await client.post(
        f"/api/v1/conversations/{conv_id}/messages",
        json={"content": "Bəli, aktivdir"},
    )
    assert response.status_code == 201
    assert len(calls) == 2
    assert all(c[1]["type"] == "message" for c in calls)


@pytest.mark.asyncio
async def test_reading_thread_does_not_clear_senders_unread(
    client, auth_user, feature_catalog, db
):
    from app.tests.test_phase7_marketplace import (
        _create_active_property,
        _create_authenticated_client,
    )

    owner = await auth_user(email="owner-read@test.az", is_verified=True)
    await auth_user(email="buyer-read@test.az")
    prop = await _create_active_property(db, owner)

    buyer_client = await _create_authenticated_client(auth_user, "buyer-read@test.az")
    owner_client = await _create_authenticated_client(auth_user, "owner-read@test.az")

    # Buyer sends the first message -> owner has 1 unread
    response = await buyer_client.post(
        "/api/v1/conversations",
        json={"property_id": str(prop.id), "message": "Salam"},
    )
    assert response.status_code == 201
    conv_id = response.json()["id"]

    unread = await owner_client.get("/api/v1/conversations/unread-count")
    assert unread.json() == {"total": 1, "conversations": 1}

    # Buyer re-opens the thread (reads their own sent message).
    # This must NOT clear the owner's unread count.
    response = await buyer_client.get(f"/api/v1/conversations/{conv_id}/messages")
    assert response.status_code == 200

    unread = await owner_client.get("/api/v1/conversations/unread-count")
    assert unread.json() == {"total": 1, "conversations": 1}

    # Once the owner reads the thread, unread drops to zero.
    response = await owner_client.get(f"/api/v1/conversations/{conv_id}/messages")
    assert response.status_code == 200
    unread = await owner_client.get("/api/v1/conversations/unread-count")
    assert unread.json() == {"total": 0, "conversations": 0}
