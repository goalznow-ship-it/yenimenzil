"""Phase 14: residential complexes (new-build developments)."""

from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_complex_crud_and_public_detail(client, auth_user, db, feature_catalog):
    from app.tests.conftest import make_property_payload

    admin = await auth_user(email="complex-admin@test.az", is_verified=True)
    admin.role = "admin"
    await db.commit()

    created = await client.post(
        "/api/v1/complexes",
        json={
            "name": "Yeni Körpü Rezidans",
            "slug": "yeni-korpu-rezidans",
            "developer_name": "Körpü İnşaat",
            "status": "under_construction",
            "city": "Bakı",
            "district": "Nəsimi",
            "completion_year": 2027,
            "total_units": 240,
            "amenities": ["parking", "elevator"],
        },
    )
    assert created.status_code == 201, created.text
    complex_id = created.json()["id"]
    assert created.json()["properties_count"] == 0

    # non-staff cannot create
    await auth_user(email="complex-regular@test.az")
    regular_client = await _other_client(client, auth_user, "complex-regular@test.az")
    denied = await regular_client.post(
        "/api/v1/complexes",
        json={"name": "Nümunə Kompleks", "slug": "numune-kompleks"},
    )
    assert denied.status_code == 403

    # re-authenticate shared client as staff
    admin2 = await auth_user(email="complex-admin2@test.az", is_verified=True)
    admin2.role = "admin"
    await db.commit()

    # property linked to the complex
    payload = make_property_payload(str(admin2.id), status="draft", media=[])
    payload["complex_id"] = complex_id
    linked = await client.post("/api/v1/properties", json=payload)
    assert linked.status_code == 201, linked.text
    submitted = await client.post(f"/api/v1/properties/{linked.json()['id']}/submit")
    assert submitted.status_code == 200, submitted.text
    assert submitted.json()["complex_id"] == complex_id

    detail = await client.get(f"/api/v1/complexes/{complex_id}")
    assert detail.status_code == 200
    data = detail.json()
    assert data["name"] == "Yeni Körpü Rezidans"
    assert data["developer_name"] == "Körpü İnşaat"
    assert data["properties_count"] == 1
    assert len(data["properties"]) >= 1
    assert data["properties"][0]["id"] == linked.json()["id"]

    listed = (await client.get("/api/v1/complexes?city=Bakı")).json()
    assert any(c["id"] == complex_id for c in listed)
    assert listed[0]["units_available"] >= 0

    patched = await client.patch(
        f"/api/v1/complexes/{complex_id}",
        json={"status": "ready", "is_verified": True},
    )
    assert patched.status_code == 200
    assert patched.json()["status"] == "ready"
    assert patched.json()["is_verified"] is True

    deleted = await client.delete(f"/api/v1/complexes/{complex_id}")
    assert deleted.status_code == 200
    gone = await client.get(f"/api/v1/complexes/{complex_id}")
    assert gone.status_code == 404


async def _other_client(client, auth_user, email):
    from app.tests.test_phase7_marketplace import _create_authenticated_client

    return await _create_authenticated_client(auth_user, email)


@pytest.mark.asyncio
async def test_complex_missing_returns_404(client, auth_user):
    import uuid

    await auth_user(email="complex-404@test.az")
    response = await client.get(f"/api/v1/complexes/{uuid.uuid4()}")
    assert response.status_code == 404
