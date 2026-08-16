"""Phase 14: listing quality scoring and duplicate detection."""

from __future__ import annotations

import pytest

from app.models.property import Property, PropertyStatus
from app.services.listing_quality import find_duplicates, score_listing


async def _create_prop(client, user_id, db, title="Tam məlumatlı mənzil"):
    from app.tests.conftest import make_property_payload

    payload = make_property_payload(
        user_id,
        status="draft",
        media=[],
    )
    payload["title"] = title
    payload["description"] = (
        "Şəhər mərkəzində təmirli, işıqlı mənzil. Uşaq bağçasına yaxın."
    )
    created = await client.post("/api/v1/properties", json=payload)
    assert created.status_code == 201, created.text
    return created.json()["id"]


@pytest.mark.asyncio
async def test_quality_score_full_listing(client, auth_user, db, feature_catalog):
    user = await auth_user(email="quality-full@test.az", is_verified=True)
    prop_id = await _create_prop(client, str(user.id), db)
    prop = await db.get(Property, prop_id)
    assert prop is not None
    report = await score_listing(db, prop)
    assert report.score >= 50
    assert report.sections["media"]["score"] == 0  # no photos yet


@pytest.mark.asyncio
async def test_quality_endpoint_owner_only(client, auth_user, db, feature_catalog):
    user = await auth_user(email="quality-owner@test.az", is_verified=True)
    prop_id = await _create_prop(client, str(user.id), db)

    response = await client.get(f"/api/v1/properties/{prop_id}/quality")
    assert response.status_code == 200, response.text
    data = response.json()
    assert "score" in data
    assert "sections" in data
    assert "warnings" in data

    from app.tests.test_phase7_marketplace import _create_authenticated_client

    await auth_user(email="quality-intruder@test.az")
    intruder = await _create_authenticated_client(auth_user, "quality-intruder@test.az")
    denied = await intruder.get(f"/api/v1/properties/{prop_id}/quality")
    assert denied.status_code == 403


@pytest.mark.asyncio
async def test_submit_stores_quality_score(client, auth_user, db, feature_catalog):
    user = await auth_user(email="quality-submit@test.az")
    prop_id = await _create_prop(client, str(user.id), db)
    response = await client.post(f"/api/v1/properties/{prop_id}/submit")
    assert response.status_code == 200, response.text
    assert response.json()["quality_score"] is not None


@pytest.mark.asyncio
async def test_duplicate_detection_finds_lookalike(
    client, auth_user, db, feature_catalog
):
    user = await auth_user(email="quality-dup@test.az", is_verified=True)
    first = await _create_prop(
        client, str(user.id), db, title="Nizami küçəsində təmirli mənzil"
    )
    second = await _create_prop(
        client, str(user.id), db, title="Nizami küçəsində təmirli mənzil"
    )

    prop = await db.get(Property, second)
    prop.status = PropertyStatus.ACTIVE.value
    first_prop = await db.get(Property, first)
    first_prop.status = PropertyStatus.ACTIVE.value
    await db.commit()

    duplicates = await find_duplicates(db, prop)
    assert duplicates, "lookalike listing not flagged"
    assert duplicates[0].property_id == first_prop.id
    assert duplicates[0].confidence >= 0.35
