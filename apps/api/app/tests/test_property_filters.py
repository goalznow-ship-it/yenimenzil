
import pytest

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


async def _verified_owner(auth_user):
    return await auth_user(is_verified=True)


@pytest.mark.asyncio
async def test_list_defaults_to_active_sale(client, auth_user, feature_catalog):
    owner = await auth_user(is_verified=True)
    await _create(client, owner, {"deal_type": "sale"})
    await _create(client, owner, {"deal_type": "rent"})
    await _create(client, owner, {"deal_type": "daily"})

    # a draft that was never submitted stays hidden
    draft = make_property_payload(owner.id)
    draft["price_history"] = []
    draft_body = (
        await client.post("/api/v1/properties", json=draft)
    ).json()
    assert draft_body["status"] == "draft"

    # a sold listing is hidden from search
    sold = (
        await client.post("/api/v1/properties", json=make_property_payload(owner.id))
    ).json()
    sold_patch = await client.patch(
        f"/api/v1/properties/{sold['id']}", json={"status": "sold"}
    )
    assert sold_patch.status_code == 200

    response = await client.get("/api/v1/properties")
    assert response.status_code == 200
    body = response.json()
    assert body["meta"]["total"] == 1
    assert body["meta"]["page"] == 1
    assert body["meta"]["page_size"] == 30
    assert body["meta"]["pages"] == 1
    assert len(body["data"]) == 1
    assert body["data"][0]["deal_type"] == "sale"


@pytest.mark.asyncio
async def test_list_deal_filter(client, auth_user, feature_catalog):
    owner = await auth_user(is_verified=True)
    await _create(client, owner, {"deal_type": "sale"})
    await _create(client, owner, {"deal_type": "rent"})
    await _create(client, owner, {"deal_type": "daily"})

    for deal in ("sale", "rent", "daily"):
        response = await client.get("/api/v1/properties", params={"deal": deal})
        assert response.json()["meta"]["total"] == 1


@pytest.mark.asyncio
async def test_list_city_filter(client, auth_user, feature_catalog):
    owner = await auth_user(is_verified=True)
    await _create(client, owner, {"location": {**make_property_payload(owner.id)["location"], "city": "Bakı"}})
    payload = make_property_payload(owner.id)
    payload["location"]["city"] = "Gəncə"
    await _create(client, owner, payload)

    response = await client.get("/api/v1/properties", params={"city": "Gəncə"})
    assert response.json()["meta"]["total"] == 1
    assert response.json()["data"][0]["city"] == "Gəncə"


@pytest.mark.asyncio
async def test_list_district_filter_normalizes_az(client, auth_user, feature_catalog):
    owner = await auth_user(is_verified=True)
    payload = make_property_payload(owner.id)
    payload["location"]["district"] = "Nərimanov"
    await _create(client, owner, payload)

    # "Nərimanov" must match a query for "Nerimanov" (ə -> e)
    response = await client.get("/api/v1/properties", params={"district": "Nerimanov"})
    assert response.status_code == 200
    assert response.json()["meta"]["total"] == 1

    # and the exact Azerbaijani spelling
    response = await client.get("/api/v1/properties", params={"district": "Nərimanov"})
    assert response.json()["meta"]["total"] == 1


@pytest.mark.asyncio
async def test_list_district_no_match(client, auth_user, feature_catalog):
    owner = await auth_user(is_verified=True)
    await _create(client, owner, {})
    response = await client.get(
        "/api/v1/properties", params={"district": "Binaqadi"}
    )
    assert response.json()["meta"]["total"] == 0


@pytest.mark.asyncio
async def test_list_property_type_filter(client, auth_user, feature_catalog):
    owner = await auth_user(is_verified=True)
    await _create(client, owner, {"property_type": "apartment"})
    await _create(client, owner, {"property_type": "house"})
    await _create(client, owner, {"property_type": "land"})

    response = await client.get(
        "/api/v1/properties", params={"property_type": "house"}
    )
    assert response.json()["meta"]["total"] == 1
    assert response.json()["data"][0]["property_type"] == "house"


@pytest.mark.asyncio
async def test_list_rooms_filter(client, auth_user, feature_catalog):
    owner = await auth_user(is_verified=True)
    await _create(client, owner, {"rooms": 1})
    await _create(client, owner, {"rooms": 2})
    await _create(client, owner, {"rooms": 3})
    await _create(client, owner, {"rooms": 4})
    await _create(client, owner, {"rooms": 5})

    response = await client.get("/api/v1/properties", params={"rooms": "2"})
    assert response.json()["meta"]["total"] == 1

    # 4plus matches any listing with 4+ rooms
    response = await client.get("/api/v1/properties", params={"rooms": "4plus"})
    assert response.json()["meta"]["total"] == 2

    response = await client.get("/api/v1/properties", params={"rooms": "1,2"})
    assert response.json()["meta"]["total"] == 2


@pytest.mark.asyncio
async def test_list_price_range_filter(client, auth_user, feature_catalog):
    owner = await auth_user(is_verified=True)
    await _create(client, owner, {"price": 50_000})
    await _create(client, owner, {"price": 150_000})
    await _create(client, owner, {"price": 300_000})

    response = await client.get(
        "/api/v1/properties", params={"min_price": 100_000, "max_price": 200_000}
    )
    assert response.json()["meta"]["total"] == 1

    response = await client.get("/api/v1/properties", params={"min_price": 100_000})
    assert response.json()["meta"]["total"] == 2


@pytest.mark.asyncio
async def test_list_area_range_filter(client, auth_user, feature_catalog):
    owner = await auth_user(is_verified=True)
    await _create(client, owner, {"area_total": 50})
    await _create(client, owner, {"area_total": 90})
    await _create(client, owner, {"area_total": 200})

    response = await client.get(
        "/api/v1/properties", params={"min_area": 60, "max_area": 150}
    )
    assert response.json()["meta"]["total"] == 1


@pytest.mark.asyncio
async def test_list_metro_filter(client, auth_user, feature_catalog):
    owner = await auth_user(is_verified=True)
    await _create(client, owner, {})
    payload = make_property_payload(owner.id)
    payload["location"]["metro"] = "İnşaatçılar"
    await _create(client, owner, payload)

    response = await client.get("/api/v1/properties", params={"metro": "İnşaatçılar"})
    assert response.json()["meta"]["total"] == 1


@pytest.mark.asyncio
async def test_list_building_and_repair_filters(client, auth_user, feature_catalog):
    owner = await auth_user(is_verified=True)
    await _create(client, owner, {"building_type": "new", "repair_status": "renovated"})
    await _create(client, owner, {"building_type": "old", "repair_status": "cosmetic"})

    response = await client.get(
        "/api/v1/properties", params={"building_type": "new"}
    )
    assert response.json()["meta"]["total"] == 1

    response = await client.get(
        "/api/v1/properties", params={"repair_status": "cosmetic"}
    )
    assert response.json()["meta"]["total"] == 1


@pytest.mark.asyncio
async def test_list_owner_only_filter(client, auth_user, feature_catalog):
    owner = await auth_user(is_verified=True)
    await _create(client, owner, {"seller_kind": "owner"})
    await _create(client, owner, {"seller_kind": "agent"})

    response = await client.get("/api/v1/properties", params={"owner_only": True})
    assert response.json()["meta"]["total"] == 1


@pytest.mark.asyncio
async def test_list_verified_only_filter(client, auth_user, feature_catalog):
    owner = await auth_user(is_verified=True)
    await _create(client, owner, {"is_verified": True})
    await _create(client, owner, {"is_verified": False})

    response = await client.get("/api/v1/properties", params={"verified_only": True})
    assert response.json()["meta"]["total"] == 1


@pytest.mark.asyncio
async def test_list_combined_filters(client, auth_user, feature_catalog):
    owner = await auth_user(is_verified=True)
    await _create(
        client,
        owner,
        {
            "deal_type": "sale",
            "property_type": "apartment",
            "price": 150_000,
            "rooms": 3,
            "is_verified": True,
        },
    )
    await _create(
        client,
        owner,
        {
            "deal_type": "sale",
            "property_type": "apartment",
            "price": 90_000,
            "rooms": 1,
            "is_verified": True,
        },
    )

    response = await client.get(
        "/api/v1/properties",
        params={
            "deal": "sale",
            "property_type": "apartment",
            "rooms": "3",
            "min_price": 100_000,
            "verified_only": True,
        },
    )
    assert response.json()["meta"]["total"] == 1
    assert response.json()["data"][0]["price"] == 150_000.0


@pytest.mark.asyncio
async def test_list_pagination(client, auth_user, feature_catalog):
    owner = await auth_user(is_verified=True)
    for i in range(7):
        await _create(client, owner, {"title": f"Elan {i}"})

    response = await client.get(
        "/api/v1/properties", params={"page": 1, "page_size": 3}
    )
    body = response.json()
    assert body["meta"]["total"] == 7
    assert body["meta"]["pages"] == 3
    assert len(body["data"]) == 3

    response = await client.get(
        "/api/v1/properties", params={"page": 3, "page_size": 3}
    )
    body = response.json()
    assert len(body["data"]) == 1

    # page beyond the last page -> empty data, stable meta
    response = await client.get(
        "/api/v1/properties", params={"page": 99, "page_size": 3}
    )
    body = response.json()
    assert body["data"] == []
    assert body["meta"]["page"] == 99

    # page_size bounds
    response = await client.get("/api/v1/properties", params={"page_size": 500})
    assert response.status_code == 422
    response = await client.get("/api/v1/properties", params={"page": 0})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_list_sort_price(client, auth_user, feature_catalog):
    owner = await auth_user(is_verified=True)
    await _create(client, owner, {"price": 300_000})
    await _create(client, owner, {"price": 100_000})
    await _create(client, owner, {"price": 200_000})

    response = await client.get(
        "/api/v1/properties", params={"sort": "price_asc", "page_size": 100}
    )
    prices = [item["price"] for item in response.json()["data"]]
    assert prices == [100_000.0, 200_000.0, 300_000.0]

    response = await client.get(
        "/api/v1/properties", params={"sort": "price_desc", "page_size": 100}
    )
    prices = [item["price"] for item in response.json()["data"]]
    assert prices == [300_000.0, 200_000.0, 100_000.0]


@pytest.mark.asyncio
async def test_list_sort_area(client, auth_user, feature_catalog):
    owner = await auth_user(is_verified=True)
    await _create(client, owner, {"area_total": 200})
    await _create(client, owner, {"area_total": 50})
    await _create(client, owner, {"area_total": 100})

    response = await client.get(
        "/api/v1/properties", params={"sort": "area_asc", "page_size": 100}
    )
    areas = [item["area_total"] for item in response.json()["data"]]
    assert areas == [50.0, 100.0, 200.0]

    response = await client.get(
        "/api/v1/properties", params={"sort": "area_desc", "page_size": 100}
    )
    areas = [item["area_total"] for item in response.json()["data"]]
    assert areas == [200.0, 100.0, 50.0]


@pytest.mark.asyncio
async def test_list_sort_newest(client, auth_user, feature_catalog):
    owner = await auth_user(is_verified=True)
    first = await _create(client, owner, {"title": "En kohne"})
    second = await _create(client, owner, {"title": "Yeni"})

    response = await client.get(
        "/api/v1/properties", params={"sort": "newest", "page_size": 100}
    )
    ids = [item["id"] for item in response.json()["data"]]
    assert ids == [second["id"], first["id"]]


@pytest.mark.asyncio
async def test_list_bbox_filter(client, auth_user, feature_catalog):
    owner = await auth_user(is_verified=True)
    inside = make_property_payload(owner.id)
    inside["location"]["latitude"] = 40.4
    inside["location"]["longitude"] = 49.85
    inside["price_history"] = []
    inside_created = (await client.post("/api/v1/properties", json=inside)).json()
    await client.post(f"/api/v1/properties/{inside_created['id']}/submit")

    outside = make_property_payload(owner.id)
    outside["location"]["latitude"] = 41.0
    outside["location"]["longitude"] = 50.0
    outside["price_history"] = []
    outside_created = (
        await client.post("/api/v1/properties", json=outside)
    ).json()

    response = await client.get(
        "/api/v1/properties",
        params={"north": 40.5, "south": 40.3, "east": 49.9, "west": 49.8},
    )
    body = response.json()
    assert body["meta"]["total"] == 1
    assert body["data"][0]["id"] != outside_created["id"]


@pytest.mark.asyncio
async def test_list_bbox_all_outside(client, auth_user, feature_catalog):
    owner = await auth_user(is_verified=True)
    payload = make_property_payload(owner.id)
    payload["location"]["latitude"] = 41.0
    payload["location"]["longitude"] = 50.0
    payload["price_history"] = []
    created = (await client.post("/api/v1/properties", json=payload)).json()
    await client.post(f"/api/v1/properties/{created['id']}/submit")

    response = await client.get(
        "/api/v1/properties",
        params={"north": 40.5, "south": 40.3, "east": 49.9, "west": 49.8},
    )
    assert response.json()["meta"]["total"] == 0


    @pytest.mark.asyncio
    async def test_list_invalid_uuid_idempotent(client, auth_user, feature_catalog):
        await auth_user(is_verified=True)
        response = await client.get("/api/v1/properties", params={"north": 91})
        assert response.status_code == 422
