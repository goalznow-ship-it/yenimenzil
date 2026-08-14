"""Tests for the DB-backed location catalog endpoints."""

import pytest

from app.services.location_seed import build_seed


@pytest.fixture(autouse=True)
async def seeded_places(db):
    db.add_all(build_seed())
    await db.commit()


async def _names(response):
    assert response.status_code == 200, response.text
    return [item["name"] for item in response.json()]


@pytest.mark.asyncio
async def test_cities_returns_baku_and_ganja(client):
    names = await _names(await client.get("/api/v1/location/cities"))
    assert "Bakı" in names
    assert "Gəncə" in names


@pytest.mark.asyncio
async def test_districts_filtered_by_city(client):
    names = await _names(
        await client.get("/api/v1/location/districts", params={"city": "Bakı"})
    )
    assert "Nərimanov" in names
    assert "Yasamal" in names
    assert "Kəpəz" not in names  # Gəncə district must not leak in


@pytest.mark.asyncio
async def test_districts_all_cities(client):
    names = await _names(await client.get("/api/v1/location/districts"))
    assert "Nərimanov" in names
    assert "Kəpəz" in names


@pytest.mark.asyncio
async def test_settlements_filtered(client):
    names = await _names(
        await client.get(
            "/api/v1/location/settlements",
            params={"city": "Bakı", "district": "Suraxanı"},
        )
    )
    assert "Qaraçuxur" in names
    assert "Mərdəkan" not in names  # Xəzər district settlement


@pytest.mark.asyncio
async def test_metros_return_baku_stations(client):
    names = await _names(
        await client.get("/api/v1/location/metros", params={"city": "Bakı"})
    )
    assert "Gənclik" in names
    assert "28 May" in names
    assert len(names) == 25


@pytest.mark.asyncio
async def test_landmarks_search(client):
    names = await _names(
        await client.get(
            "/api/v1/location/landmarks", params={"city": "Bakı", "q": "Mall"}
        )
    )
    assert "28 Mall" in names
    assert "Gənclik Mall" in names
    assert "Qız Qalası" not in names


@pytest.mark.asyncio
async def test_streets_empty_until_seeded(client):
    response = await client.get("/api/v1/location/streets", params={"q": "Nizami"})
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_search_grouped_results(client):
    response = await client.get("/api/v1/location/search", params={"q": "Gənc"})
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["query"] == "Gənc"
    kinds = {item["kind"] for items in body["results"].values() for item in items}
    assert "city" in kinds  # Gəncə city
    assert "metro" in kinds  # Gənclik metro
    assert "landmark" in kinds  # Gənclik Mall


@pytest.mark.asyncio
async def test_search_scoped_to_city(client):
    response = await client.get(
        "/api/v1/location/search", params={"q": "Mərdəkan", "city": "Gəncə"}
    )
    body = response.json()
    found = [item["name"] for items in body["results"].values() for item in items]
    assert "Mərdəkan" not in found


@pytest.mark.asyncio
async def test_hierarchy_shape(client):
    response = await client.get("/api/v1/location/hierarchy")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["country"] == "Azərbaycan"
    cities = {region["name"] for region in body["regions"]}
    assert "Bakı" in cities
    bakı = next(r for r in body["regions"] if r["name"] == "Bakı")
    district_names = {d["name"] for d in bakı["districts"]}
    assert "Nərimanov" in district_names
    assert "Yasamal" in district_names


@pytest.mark.asyncio
async def test_search_requires_query(client):
    response = await client.get("/api/v1/location/search")
    assert response.status_code == 422
