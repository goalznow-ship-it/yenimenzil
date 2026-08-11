import uuid

import pytest

from app.tests.conftest import make_property_payload


@pytest.mark.asyncio
async def test_create_property_roundtrip(client, auth_user, feature_catalog):
    owner = await auth_user(is_verified=True)
    created = (
        await client.post(
            "/api/v1/properties",
            json=make_property_payload(owner.id),
        )
    ).json()
    await client.post(f"/api/v1/properties/{created['id']}/submit")
    response = await client.get(f"/api/v1/properties/{created['id']}")
    assert response.status_code == 200
    body = response.json()

    assert body["reference_code"] == "AB1001"
    assert body["slug"].endswith("-1001")
    assert body["title"] == "Test elan 3 otaqli manzil"
    assert body["deal_type"] == "sale"
    assert body["price"] == 150000.0
    assert body["rooms"] == 3
    assert body["status"] == "active"
    assert body["is_verified"] is False
    assert body["has_price_drop"] is True
    assert body["features"] == ["elevator", "mortgage"]
    assert body["location"]["latitude"] == 40.4093
    assert body["location"]["longitude"] == 49.8502
    assert body["location"]["district"] == "Nərimanov"
    assert len(body["media"]) == 2
    assert body["media"][0]["is_cover"] is True
    assert len(body["price_history"]) == 2
    assert body["seller"]["name"] == "Test Sahib"
    assert body["seller"]["kind"] == "owner"
    assert body["seller"]["active_listings"] == 1
    assert body["latitude"] == 40.4093
    assert body["longitude"] == 49.8502
    assert body["address_text"] == "Nərimanov r., Gənclik"
    assert body["metro"] == "Gənclik"


@pytest.mark.asyncio
async def test_create_reference_codes_increment(client, auth_user, feature_catalog):
    owner = await auth_user(is_verified=True)
    payload = make_property_payload(owner.id)
    for expected in ("AB1001", "AB1002"):
        response = await client.post("/api/v1/properties", json=payload)
        assert response.status_code == 201
        assert response.json()["reference_code"] == expected


@pytest.mark.asyncio
async def test_create_for_another_user_rejected(client, auth_user, feature_catalog):
    await auth_user()
    response = await client.post(
        "/api/v1/properties",
        json=make_property_payload(uuid.uuid4()),
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_create_requires_auth(client, feature_catalog):
    response = await client.post(
        "/api/v1/properties",
        json=make_property_payload(uuid.uuid4()),
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_create_rejects_unknown_feature(client, auth_user, feature_catalog):
    owner = await auth_user()
    payload = make_property_payload(
        owner.id, features=["not-a-real-feature"]
    )
    response = await client.post("/api/v1/properties", json=payload)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_rejects_invalid_price(client, auth_user):
    owner = await auth_user()
    payload = make_property_payload(owner.id, price=-100)
    response = await client.post("/api/v1/properties", json=payload)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_rejects_invalid_coordinates(client, auth_user):
    owner = await auth_user()
    payload = make_property_payload(owner.id)
    payload["location"]["latitude"] = 95
    response = await client.post("/api/v1/properties", json=payload)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_rejects_active_status_for_regular_user(
    client, auth_user, feature_catalog
):
    owner = await auth_user()
    payload = make_property_payload(owner.id, status="active")
    response = await client.post("/api/v1/properties", json=payload)
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_create_active_allowed_for_moderator(
    client, auth_user, feature_catalog
):
    owner = await auth_user(role="moderator")
    payload = make_property_payload(owner.id, status="active")
    response = await client.post("/api/v1/properties", json=payload)
    assert response.status_code == 201
    assert response.json()["status"] == "active"


@pytest.mark.asyncio
async def test_get_property_by_id(client, auth_user, feature_catalog):
    owner = await auth_user()
    created = (
        await client.post(
            "/api/v1/properties",
            json=make_property_payload(owner.id),
        )
    ).json()

    response = await client.get(f"/api/v1/properties/{created['id']}")
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == created["id"]
    assert body["description"] == "Gözəl mənzil, mərkəzdə."
    assert body["bedrooms"] == 2
    assert body["document_type"] == "extract"
    assert body["mortgage_available"] is True
    assert body["created_at"] is not None
    assert body["updated_at"] is not None


@pytest.mark.asyncio
async def test_get_property_not_found(client):
    response = await client.get(f"/api/v1/properties/{uuid.uuid4()}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_property_invalid_uuid(client):
    response = await client.get("/api/v1/properties/not-a-uuid")
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_patch_property_partial(client, auth_user, feature_catalog):
    owner = await auth_user()
    created = (
        await client.post(
            "/api/v1/properties",
            json=make_property_payload(owner.id),
        )
    ).json()

    response = await client.patch(
        f"/api/v1/properties/{created['id']}",
        json={"price": 148000, "is_premium": True},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["price"] == 148000.0
    assert body["is_premium"] is True
    assert body["title"] == created["title"]


@pytest.mark.asyncio
async def test_patch_updates_location_and_features(client, auth_user, feature_catalog):
    owner = await auth_user()
    created = (
        await client.post(
            "/api/v1/properties",
            json=make_property_payload(owner.id),
        )
    ).json()

    response = await client.patch(
        f"/api/v1/properties/{created['id']}",
        json={
            "location": {
                "latitude": 40.1,
                "longitude": 49.1,
                "address_text": "Yeni ünvan",
                "city": "Gəncə",
                "district": "Kəpəz",
            },
            "features": ["parking", "balcony"],
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["location"]["latitude"] == 40.1
    assert body["location"]["city"] == "Gəncə"
    assert body["features"] == ["parking", "balcony"]
    assert body["latitude"] == 40.1


@pytest.mark.asyncio
async def test_patch_unknown_feature_rejected(client, auth_user, feature_catalog):
    owner = await auth_user()
    created = (
        await client.post(
            "/api/v1/properties",
            json=make_property_payload(owner.id),
        )
    ).json()
    response = await client.patch(
        f"/api/v1/properties/{created['id']}", json={"features": ["nope"]}
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_patch_requires_auth(client):
    response = await client.patch(
        f"/api/v1/properties/{uuid.uuid4()}", json={"price": 1}
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_patch_not_found(client, auth_user):
    await auth_user()
    response = await client.patch(
        f"/api/v1/properties/{uuid.uuid4()}", json={"price": 1}
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_patch_other_users_property_rejected(client, auth_user, feature_catalog):
    owner = await auth_user()
    created = (
        await client.post(
            "/api/v1/properties",
            json=make_property_payload(owner.id),
        )
    ).json()

    other = await auth_user(email="other@test.az")
    response = await client.patch(
        f"/api/v1/properties/{created['id']}", json={"price": 1}
    )
    assert response.status_code == 403
    assert other.id != owner.id


@pytest.mark.asyncio
async def test_delete_property(client, auth_user, feature_catalog):
    owner = await auth_user()
    created = (
        await client.post(
            "/api/v1/properties",
            json=make_property_payload(owner.id),
        )
    ).json()

    response = await client.delete(f"/api/v1/properties/{created['id']}")
    assert response.status_code == 204

    response = await client.get(f"/api/v1/properties/{created['id']}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_other_users_property_rejected(
    client, auth_user, feature_catalog
):
    owner = await auth_user()
    created = (
        await client.post(
            "/api/v1/properties",
            json=make_property_payload(owner.id),
        )
    ).json()

    await auth_user(email="other@test.az")
    response = await client.delete(f"/api/v1/properties/{created['id']}")
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_delete_not_found(client, auth_user):
    await auth_user()
    response = await client.delete(f"/api/v1/properties/{uuid.uuid4()}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_similar_properties(client, auth_user, feature_catalog):
    owner = await auth_user(is_verified=True)
    base = make_property_payload(owner.id)
    base["price_history"] = []
    created = (await client.post("/api/v1/properties", json=base)).json()
    await client.post(f"/api/v1/properties/{created['id']}/submit")

    same = make_property_payload(owner.id, title="Benzer elan", price=160000)
    same["price_history"] = []
    same_created = (await client.post("/api/v1/properties", json=same)).json()
    await client.post(f"/api/v1/properties/{same_created['id']}/submit")

    other_type = make_property_payload(
        owner.id, title="Villa", property_type="villa"
    )
    other_type["price_history"] = []
    other_type_created = (await client.post("/api/v1/properties", json=other_type)).json()
    await client.post(f"/api/v1/properties/{other_type_created['id']}/submit")

    rent = make_property_payload(
        owner.id, title="Kiraye", deal_type="rent", price=800
    )
    rent["price_history"] = []
    rent_created = (await client.post("/api/v1/properties", json=rent)).json()
    await client.post(f"/api/v1/properties/{rent_created['id']}/submit")

    response = await client.get(f"/api/v1/properties/{created['id']}/similar")
    assert response.status_code == 200
    ids = {item["id"] for item in response.json()}
    assert ids == {same_created["id"]}
    assert created["id"] not in ids
    assert other_type_created["id"] not in ids
    assert rent_created["id"] not in ids
