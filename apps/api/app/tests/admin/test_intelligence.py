import pytest


async def _superadmin_login(client, auth_user):
    await auth_user(email="superadmin@test.az", role="super_admin")
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": "superadmin@test.az", "password": "supersecret1"},
    )
    assert login_response.status_code == 200


def _create_properties(client, owner_id, base_title):
    raise NotImplementedError


@pytest.mark.asyncio
async def _make_active_listings(client, db, auth_user, count=3):
    """Create `count` approved/active listings for the same owner in the
    same district so price intelligence and comparables have data."""
    from sqlalchemy import select

    from app.models.property import Property
    from app.tests.conftest import make_property_payload

    await _superadmin_login(client, auth_user)
    owner = await auth_user(email="owner@test.az", role="owner")

    created = []
    for i in range(count):
        payload = make_property_payload(
            owner.id,
            title=f"Test elan {i}",
            price=100000 + i * 5000,
            location={
                "latitude": 40.4093,
                "longitude": 49.8502,
                "address_text": "Nərimanov r., Gənclik",
                "city": "Bakı",
                "district": "Nərimanov",
                "neighborhood": "Gənclik",
                "metro": "Gənclik",
            },
        )
        response = await client.post("/api/v1/properties", json=payload)
        assert response.status_code == 201, response.text
        created.append(response.json()["id"])

    # Re-login as super admin to override the cookies set by auth_user for owner
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": "superadmin@test.az", "password": "supersecret1"},
    )
    assert login_response.status_code == 200

    # Move created listings to pending_review so they can be approved
    result = await db.execute(select(Property).where(Property.id.in_(created)))
    for prop in result.scalars().all():
        prop.status = "pending_review"
    await db.commit()

    # Approve all via the admin endpoint
    for prop_id in created:
        response = await client.post(f"/api/v1/admin/listings/{prop_id}/approve")
        assert response.status_code == 200, response.text

    result = await db.execute(select(Property).where(Property.id.in_(created)))
    props = result.scalars().all()
    for prop in props:
        await db.refresh(prop)
        status = (
            prop.status.value if hasattr(prop.status, "value") else str(prop.status)
        )
        assert status == "active", f"expected active, got {status}"
    return created, props


@pytest.mark.asyncio
async def test_admin_price_intelligence_requires_auth(client):
    response = await client.get("/api/v1/admin/price-intelligence")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_admin_price_intelligence(client, auth_user, db):
    await _make_active_listings(client, db, auth_user, count=3)

    # Re-login as super admin (owner login overwrote the cookie)
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": "superadmin@test.az", "password": "supersecret1"},
    )
    assert login_response.status_code == 200

    response = await client.get("/api/v1/admin/price-intelligence")
    assert response.status_code == 200
    data = response.json()
    assert "segments" in data
    baku_segments = [
        s
        for s in data["segments"]
        if s["city"] == "Bakı" and s["district"] == "Nərimanov"
    ]
    assert baku_segments, data["segments"]
    segment = baku_segments[0]
    assert segment["count"] == 3
    assert segment["avg_price"] == 105000.0
    assert segment["median_price"] == 105000.0
    assert segment["median_price_per_m2"] == 1312.5

    filtered = await client.get(
        "/api/v1/admin/price-intelligence?deal_type=sale&property_type=apartment"
    )
    assert filtered.status_code == 200


@pytest.mark.asyncio
async def test_admin_comparables(client, auth_user, db):
    __created, props = await _make_active_listings(client, db, auth_user, count=3)
    target = props[0]

    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": "superadmin@test.az", "password": "supersecret1"},
    )
    assert login_response.status_code == 200

    response = await client.get(f"/api/v1/admin/listings/{target.id}/comparables")
    assert response.status_code == 200
    data = response.json()
    assert data["property_id"] == str(target.id)
    assert data["comparable_count"] == 2
    assert all(c["id"] != str(target.id) for c in data["comparables"])
    assert data["price_percentile"] is not None
    assert data["criteria"]["district"] == "Nərimanov"


@pytest.mark.asyncio
async def test_admin_comparables_404(client, auth_user):
    import uuid

    await _superadmin_login(client, auth_user)
    response = await client.get(f"/api/v1/admin/listings/{uuid.uuid4()}/comparables")
    assert response.status_code == 404
