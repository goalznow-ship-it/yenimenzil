"""Tests for the Phase 5 search filters and sorts."""
from datetime import UTC, datetime, timedelta

import pytest

from app.models.favorite import Favorite
from app.models.property import Property
from app.tests.conftest import make_property_payload


async def _create(client, user, payload_overrides=None, **kwargs):
    payload = make_property_payload(user.id)
    if payload_overrides:
        payload.update(payload_overrides)
    payload["price_history"] = []
    created = (
        await client.post("/api/v1/properties", json=payload, **kwargs)
    ).json()
    response = await client.post(f"/api/v1/properties/{created['id']}/submit")
    assert response.status_code == 200, response.text
    return response.json()


@pytest.mark.asyncio
async def test_list_landmark_filter(client, auth_user, feature_catalog):
    owner = await auth_user(is_verified=True)
    payload = make_property_payload(owner.id)
    payload["location"]["landmark"] = "Gənclik Mall"
    payload["price_history"] = []
    created = (await client.post("/api/v1/properties", json=payload)).json()
    await client.post(f"/api/v1/properties/{created['id']}/submit")
    await _create(client, owner, {})

    response = await client.get(
        "/api/v1/properties", params={"landmark": "Gənclik Mall"}
    )
    assert response.json()["meta"]["total"] == 1


@pytest.mark.asyncio
async def test_list_area_land_filter(client, auth_user, feature_catalog):
    owner = await auth_user(is_verified=True)
    await _create(client, owner, {"property_type": "land", "area_land": 800})
    await _create(client, owner, {"property_type": "land", "area_land": 1200})

    response = await client.get(
        "/api/v1/properties",
        params={"property_type": "land", "min_area_land": 700, "max_area_land": 1000},
    )
    assert response.json()["meta"]["total"] == 1


@pytest.mark.asyncio
async def test_list_mortgage_furnished_heating_document_filters(
    client, auth_user, feature_catalog
):
    owner = await auth_user(is_verified=True)
    await _create(
        client,
        owner,
        {
            "mortgage_available": True,
            "furnished": True,
            "heating": "central",
            "document_type": "extract",
        },
    )
    await _create(
        client,
        owner,
        {"mortgage_available": False, "furnished": False, "document_type": "certificate"},
    )

    assert (await client.get("/api/v1/properties", params={"mortgage": True})).json()["meta"]["total"] == 1
    assert (await client.get("/api/v1/properties", params={"furnished": True})).json()["meta"]["total"] == 1
    assert (await client.get("/api/v1/properties", params={"heating": "central"})).json()["meta"]["total"] == 1
    assert (await client.get("/api/v1/properties", params={"document_type": "extract"})).json()["meta"]["total"] == 1


@pytest.mark.asyncio
async def test_list_floor_filters(client, auth_user, feature_catalog):
    owner = await auth_user(is_verified=True)
    await _create(client, owner, {"floor": 1, "total_floors": 12})
    await _create(client, owner, {"floor": 5, "total_floors": 12})
    await _create(client, owner, {"floor": 12, "total_floors": 12})

    assert (await client.get("/api/v1/properties", params={"floor": 5})).json()["meta"]["total"] == 1
    assert (await client.get("/api/v1/properties", params={"total_floors": 12})).json()["meta"]["total"] == 3
    assert (await client.get("/api/v1/properties", params={"is_first_floor": True})).json()["meta"]["total"] == 1
    assert (await client.get("/api/v1/properties", params={"is_last_floor": True})).json()["meta"]["total"] == 1


@pytest.mark.asyncio
async def test_list_room_counts_filter(client, auth_user, feature_catalog):
    owner = await auth_user(is_verified=True)
    await _create(client, owner, {"bedrooms": 1, "bathrooms": 1})
    await _create(client, owner, {"bedrooms": 2, "bathrooms": 1})
    await _create(client, owner, {"bedrooms": 3, "bathrooms": 2})

    response = await client.get(
        "/api/v1/properties", params={"min_bedrooms": 2, "max_bedrooms": 3}
    )
    assert response.json()["meta"]["total"] == 2

    response = await client.get(
        "/api/v1/properties", params={"min_bathrooms": 2}
    )
    assert response.json()["meta"]["total"] == 1


@pytest.mark.asyncio
async def test_list_construction_year_filter(client, auth_user, feature_catalog):
    owner = await auth_user(is_verified=True)
    await _create(client, owner, {"construction_year": 2000})
    await _create(client, owner, {"construction_year": 2015})
    await _create(client, owner, {"construction_year": 2024})

    response = await client.get(
        "/api/v1/properties",
        params={"min_construction_year": 2005, "max_construction_year": 2020},
    )
    assert response.json()["meta"]["total"] == 1


@pytest.mark.asyncio
async def test_list_seller_kind_filter(client, auth_user, feature_catalog):
    owner = await auth_user(is_verified=True)
    await _create(client, owner, {"seller_kind": "owner"})
    await _create(client, owner, {"seller_kind": "agent"})

    response = await client.get(
        "/api/v1/properties", params={"seller_kind": "agent"}
    )
    assert response.json()["meta"]["total"] == 1


@pytest.mark.asyncio
async def test_list_keyword_filter(client, auth_user, feature_catalog):
    owner = await auth_user(is_verified=True)
    await _create(client, owner, {"title": "Gənclik yaxınlığında 3 otaqlı"})
    await _create(client, owner, {"title": "Sahil bağında villa"})

    response = await client.get("/api/v1/properties", params={"keyword": "Gənclik"})
    assert response.json()["meta"]["total"] == 1


@pytest.mark.asyncio
async def test_list_features_and_filter(client, auth_user, feature_catalog):
    owner = await auth_user(is_verified=True)
    # elevator matches property with only elevator feature
    await _create(client, owner, {"features": ["elevator"]})
    # mortgage matches property with only mortgage feature
    await _create(client, owner, {"features": ["mortgage"]})

    # elevator-only property should appear with features=elevator
    r1 = await client.get("/api/v1/properties", params={"features": "elevator"})
    assert r1.json()["meta"]["total"] == 1

    # mortgage-only property should appear with features=mortgage
    r2 = await client.get("/api/v1/properties", params={"features": "mortgage"})
    assert r2.json()["meta"]["total"] == 1


@pytest.mark.asyncio
async def test_list_promoted_only_filter(client, auth_user, feature_catalog, db):
    owner = await auth_user(is_verified=True)
    promoted = await _create(client, owner, {"title": "Promoted"})
    await _create(client, owner, {"title": "Normal"})

    prop = await db.get(Property, promoted["id"])
    prop.is_promoted = True
    await db.commit()

    response = await client.get("/api/v1/properties", params={"promoted_only": True})
    assert response.json()["meta"]["total"] == 1


@pytest.mark.asyncio
async def test_list_price_dropped_filter(client, auth_user, feature_catalog):
    owner = await auth_user(is_verified=True)
    # explicit price history: first 200k (older) -> latest 150k (newer) => dropped
    payload = make_property_payload(owner.id)
    payload["price"] = 150_000
    payload["price_history"] = [
        {"price": 200_000, "recorded_at": "2022-01-01T00:00:00+00:00"},
        {"price": 150_000, "recorded_at": "2023-01-01T00:00:00+00:00"},
    ]
    created = (await client.post("/api/v1/properties", json=payload)).json()
    await client.post(f"/api/v1/properties/{created['id']}/submit")
    await _create(client, owner, {"price": 150_000})

    response = await client.get("/api/v1/properties", params={"price_dropped": True})
    assert response.json()["meta"]["total"] == 1


@pytest.mark.asyncio
async def test_list_published_after_filter(client, auth_user, feature_catalog, db):
    owner = await auth_user(is_verified=True)
    old = await _create(client, owner, {"title": "Köhnə"})
    new = await _create(client, owner, {"title": "Yeni"})

    old_prop = await db.get(Property, old["id"])
    old_prop.published_at = datetime.now(UTC) - timedelta(days=30)
    new_prop = await db.get(Property, new["id"])
    new_prop.published_at = datetime.now(UTC)
    await db.commit()

    response = await client.get(
        "/api/v1/properties", params={"published_after": datetime.now(UTC) - timedelta(days=7)}
    )
    assert response.json()["meta"]["total"] == 1
    assert response.json()["data"][0]["id"] == new["id"]


@pytest.mark.asyncio
async def test_list_sort_oldest(client, auth_user, feature_catalog, db):
    owner = await auth_user(is_verified=True)
    first = await _create(client, owner, {"title": "En kohne"})
    second = await _create(client, owner, {"title": "Yeni"})

    first_prop = await db.get(Property, first["id"])
    first_prop.published_at = datetime.now(UTC) - timedelta(days=10)
    second_prop = await db.get(Property, second["id"])
    second_prop.published_at = datetime.now(UTC) - timedelta(days=1)
    await db.commit()

    response = await client.get(
        "/api/v1/properties", params={"sort": "oldest", "page_size": 100}
    )
    ids = [item["id"] for item in response.json()["data"]]
    assert ids == [first["id"], second["id"]]


@pytest.mark.asyncio
async def test_list_sort_price_per_m2(client, auth_user, feature_catalog):
    owner = await auth_user(is_verified=True)
    await _create(client, owner, {"price": 300_000, "area_total": 100})  # 3000/m2
    await _create(client, owner, {"price": 200_000, "area_total": 100})  # 2000/m2
    await _create(client, owner, {"price": 150_000, "area_total": 100})  # 1500/m2

    response = await client.get(
        "/api/v1/properties", params={"sort": "price_per_m2_asc", "page_size": 100}
    )
    prices = [item["price"] for item in response.json()["data"]]
    assert prices == [150_000.0, 200_000.0, 300_000.0]

    response = await client.get(
        "/api/v1/properties", params={"sort": "price_per_m2_desc", "page_size": 100}
    )
    prices = [item["price"] for item in response.json()["data"]]
    assert prices == [300_000.0, 200_000.0, 150_000.0]


@pytest.mark.asyncio
async def test_list_sort_views(client, auth_user, feature_catalog, db):
    owner = await auth_user(is_verified=True)
    low = await _create(client, owner, {"title": "Az baxilan"})
    high = await _create(client, owner, {"title": "Cox baxilan"})

    low_prop = await db.get(Property, low["id"])
    low_prop.views = 5
    high_prop = await db.get(Property, high["id"])
    high_prop.views = 50
    await db.commit()

    response = await client.get(
        "/api/v1/properties", params={"sort": "views", "page_size": 100}
    )
    ids = [item["id"] for item in response.json()["data"]]
    assert ids == [high["id"], low["id"]]


@pytest.mark.asyncio
async def test_list_sort_favorites(client, auth_user, feature_catalog, db):
    owner = await auth_user(is_verified=True)
    popular = await _create(client, owner, {"title": "Popular"})
    lonely = await _create(client, owner, {"title": "Tenha"})

    fan = await auth_user("fan@test.az")
    db.add(Favorite(user_id=fan.id, property_id=popular["id"]))
    await db.commit()

    response = await client.get(
        "/api/v1/properties", params={"sort": "favorites", "page_size": 100}
    )
    ids = [item["id"] for item in response.json()["data"]]
    assert ids == [popular["id"], lonely["id"]]