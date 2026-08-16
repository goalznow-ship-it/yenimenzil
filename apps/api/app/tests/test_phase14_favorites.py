"""Phase 14: favorites collections (folders, move, default list, analytics)."""

from __future__ import annotations

import pytest
from sqlalchemy import select

from app.models.analytics import AnalyticsEvent
from app.models.enums import AnalyticsEventType


@pytest.mark.asyncio
async def test_collection_lifecycle(client, auth_user, feature_catalog, db):
    await auth_user(email="fav-life@test.az", is_verified=True)

    response = await client.post(
        "/api/v1/favorites/collections", json={"name": "Mənzil axtarışı"}
    )
    assert response.status_code == 201, response.text
    collection = response.json()
    assert collection["name"] == "Mənzil axtarışı"
    assert collection["is_default"] is False
    assert collection["favorite_count"] == 0

    response = await client.post(
        "/api/v1/favorites/collections", json={"name": "Mənzil axtarışı"}
    )
    assert response.status_code == 409

    response = await client.patch(
        f"/api/v1/favorites/collections/{collection['id']}",
        json={"name": "Yeni ad"},
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Yeni ad"

    collections = await client.get("/api/v1/favorites/collections")
    assert collections.status_code == 200
    assert len(collections.json()) == 1

    response = await client.delete(f"/api/v1/favorites/collections/{collection['id']}")
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_move_favorite_between_collections(
    client, auth_user, feature_catalog, db
):
    from app.tests.test_phase7_marketplace import _create_active_property

    owner = await auth_user(email="fav-owner@test.az", is_verified=True)
    await auth_user(email="fav-move@test.az")
    prop = await _create_active_property(db, owner)

    await client.post(f"/api/v1/favorites/{prop.id}")
    coll = (
        await client.post("/api/v1/favorites/collections", json={"name": "Kolleksiya"})
    ).json()

    # Move the favorite into the collection
    response = await client.patch(
        f"/api/v1/favorites/{prop.id}", json={"collection_id": coll["id"]}
    )
    assert response.status_code == 200

    # Collection view contains it; default view does not
    in_coll = await client.get(
        "/api/v1/favorites", params={"collection_id": coll["id"]}
    )
    assert [p["id"] for p in in_coll.json()] == [str(prop.id)]
    default = await client.get("/api/v1/favorites")
    assert default.json() == []

    # Move back to default
    response = await client.patch(
        f"/api/v1/favorites/{prop.id}", json={"collection_id": None}
    )
    assert response.status_code == 200
    default = await client.get("/api/v1/favorites")
    assert [p["id"] for p in default.json()] == [str(prop.id)]


@pytest.mark.asyncio
async def test_add_favorite_to_collection_via_body(
    client, auth_user, feature_catalog, db
):
    from app.tests.test_phase7_marketplace import _create_active_property

    owner = await auth_user(email="fav-owner2@test.az", is_verified=True)
    await auth_user(email="fav-body@test.az")
    prop = await _create_active_property(db, owner)
    coll = (
        await client.post("/api/v1/favorites/collections", json={"name": "Direkt"})
    ).json()

    response = await client.post(
        f"/api/v1/favorites/{prop.id}", json={"collection_id": coll["id"]}
    )
    assert response.status_code == 201

    in_coll = await client.get(
        "/api/v1/favorites", params={"collection_id": coll["id"]}
    )
    assert [p["id"] for p in in_coll.json()] == [str(prop.id)]


@pytest.mark.asyncio
async def test_collection_ownership(client, auth_user, feature_catalog, db):
    await auth_user(email="fav-owner3@test.az", is_verified=True)
    coll = (
        await client.post("/api/v1/favorites/collections", json={"name": "Sahib"})
    ).json()

    other = await _create_other_client(auth_user, "fav-other@test.az")
    response = await other.patch(
        f"/api/v1/favorites/collections/{coll['id']}", json={"name": "Oğurluq"}
    )
    assert response.status_code == 404
    response = await other.get(
        "/api/v1/favorites", params={"collection_id": coll["id"]}
    )
    assert response.status_code == 404
    response = await other.delete(f"/api/v1/favorites/collections/{coll['id']}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_favorite_events_logged_server_side(
    client, auth_user, feature_catalog, db
):
    from app.tests.test_phase7_marketplace import _create_active_property

    owner = await auth_user(email="fav-events@test.az", is_verified=True)
    user = await auth_user(email="fav-events-user@test.az")
    prop = await _create_active_property(db, owner)

    await client.post(f"/api/v1/favorites/{prop.id}")
    events = (
        (
            await db.execute(
                select(AnalyticsEvent).where(AnalyticsEvent.property_id == prop.id)
            )
        )
        .scalars()
        .all()
    )
    assert [e.event_type for e in events] == [
        AnalyticsEventType.PROPERTY_FAVORITE.value
    ]
    assert events[0].user_id == user.id

    await client.delete(f"/api/v1/favorites/{prop.id}")
    events = (
        (
            await db.execute(
                select(AnalyticsEvent)
                .where(AnalyticsEvent.property_id == prop.id)
                .order_by(AnalyticsEvent.created_at)
            )
        )
        .scalars()
        .all()
    )
    assert [e.event_type for e in events] == [
        AnalyticsEventType.PROPERTY_FAVORITE.value,
        AnalyticsEventType.PROPERTY_UNFAVORITE.value,
    ]


@pytest.mark.asyncio
async def test_default_collection_immutable(client, auth_user, feature_catalog, db):
    await auth_user(email="fav-default@test.az", is_verified=True)
    collections = (await client.get("/api/v1/favorites/collections")).json()
    assert collections == []


async def _create_other_client(auth_user, email):
    from httpx import ASGITransport, AsyncClient

    from app.main import app

    transport = ASGITransport(app=app)
    other = AsyncClient(transport=transport, base_url="http://test")
    await auth_user(email=email)
    login = await other.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "supersecret1"},
    )
    assert login.status_code == 200
    return other
