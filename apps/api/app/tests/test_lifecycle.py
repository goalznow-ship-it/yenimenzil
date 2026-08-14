"""Phase 10: listing lifecycle tests (duplicate, renew, deactivate, reactivate)."""

from __future__ import annotations

import uuid

import pytest

from app.tests.conftest import make_property_payload


@pytest.fixture()
async def seller(client, auth_user):
    user = await auth_user(email="life@test.az", is_verified=True)
    return {"user": user}


@pytest.fixture()
async def listing(client, seller, feature_catalog):
    payload = make_property_payload(seller["user"].id)
    resp = await client.post("/api/v1/properties", json=payload)
    assert resp.status_code == 201, resp.text
    submitted = await client.post(f"/api/v1/properties/{resp.json()['id']}/submit")
    assert submitted.status_code == 200, submitted.text
    return submitted.json()


async def test_duplicate_creates_draft(client, seller, listing):
    resp = await client.post(f"/api/v1/properties/{listing['id']}/duplicate")
    assert resp.status_code == 200, resp.text
    clone = resp.json()
    assert clone["id"] != listing["id"]
    assert clone["reference_code"] != listing["reference_code"]
    assert clone["slug"] != listing["slug"]
    assert clone["status"] == "draft"
    assert clone["title"] == f"{listing['title']} (surət)"
    assert clone["price"] == listing["price"]
    assert len(clone["media"]) == len(listing["media"])
    assert clone["media"][0]["url"] == listing["media"][0]["url"]


async def test_duplicate_requires_ownership(client, seller, listing, auth_user):
    await auth_user(email="life2@test.az")
    resp = await client.post(f"/api/v1/properties/{listing['id']}/duplicate")
    assert resp.status_code == 403


async def test_renew_expired_listing(client, seller, listing):
    from sqlalchemy import update

    from app.db.session import async_session_factory
    from app.models.property import Property

    async with async_session_factory() as db:
        await db.execute(
            update(Property)
            .where(Property.id == uuid.UUID(listing["id"]))
            .values(status="expired")
        )
        await db.commit()

    resp = await client.post(f"/api/v1/properties/{listing['id']}/renew")
    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "active"
    assert resp.json()["expires_at"] is not None


async def test_renew_active_listing_rejected(client, seller, listing):
    resp = await client.post(f"/api/v1/properties/{listing['id']}/renew")
    assert resp.status_code == 400


async def test_deactivate_and_reactivate(client, seller, listing):
    deact = await client.post(f"/api/v1/properties/{listing['id']}/deactivate")
    assert deact.status_code == 200
    assert deact.json()["status"] == "archived"

    react = await client.post(f"/api/v1/properties/{listing['id']}/reactivate")
    assert react.status_code == 200
    assert react.json()["status"] == "active"


async def test_mark_sold_allowed_via_patch(client, seller, listing):
    resp = await client.patch(
        f"/api/v1/properties/{listing['id']}",
        json={"status": "sold"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "sold"


async def test_deactivate_draft_rejected(client, seller, listing):
    from sqlalchemy import update

    from app.db.session import async_session_factory
    from app.models.property import Property

    async with async_session_factory() as db:
        await db.execute(
            update(Property)
            .where(Property.id == uuid.UUID(listing["id"]))
            .values(status="draft")
        )
        await db.commit()

    resp = await client.post(f"/api/v1/properties/{listing['id']}/deactivate")
    assert resp.status_code == 400
