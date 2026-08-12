import pytest


@pytest.mark.asyncio
async def test_admin_analytics_requires_auth(client):
    response = await client.get("/api/v1/admin/analytics/marketplace")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_admin_analytics_marketplace(client, auth_user, db):
    await auth_user(email="superadmin@test.az", role="super_admin")
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": "superadmin@test.az", "password": "supersecret1"},
    )
    assert login_response.status_code == 200

    # Record some analytics events
    from app.models.analytics import AnalyticsEvent
    from app.models.enums import AnalyticsEventType

    for event_type in (
        AnalyticsEventType.PROPERTY_VIEW,
        AnalyticsEventType.PROPERTY_VIEW,
        AnalyticsEventType.PROPERTY_FAVORITE,
        AnalyticsEventType.PHONE_REVEAL,
        AnalyticsEventType.SEARCH,
    ):
        db.add(AnalyticsEvent(event_type=event_type.value))
    await db.commit()

    response = await client.get("/api/v1/admin/analytics/marketplace")
    assert response.status_code == 200
    data = response.json()
    assert data["period_days"] == 30
    assert data["views"] == 2
    assert data["favorites"] == 1
    assert data["phone_reveals"] == 1
    assert data["searches"] == 1
    assert "listings_by_type" in data
    assert "top_listings" in data


@pytest.mark.asyncio
async def test_admin_analytics_days_param(client, auth_user):
    await auth_user(email="superadmin@test.az", role="super_admin")
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": "superadmin@test.az", "password": "supersecret1"},
    )
    assert login_response.status_code == 200
    response = await client.get("/api/v1/admin/analytics/marketplace?days=7")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_admin_locations_requires_auth(client):
    response = await client.get("/api/v1/admin/locations")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_admin_locations_overview(client, auth_user, db):
    from app.tests.conftest import make_property_payload

    await auth_user(email="superadmin@test.az", role="super_admin")
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": "superadmin@test.az", "password": "supersecret1"},
    )
    assert login_response.status_code == 200

    owner = await auth_user(email="owner@test.az", role="owner")
    response = await client.post(
        "/api/v1/properties",
        json=make_property_payload(owner.id),
    )
    assert response.status_code == 201

    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": "superadmin@test.az", "password": "supersecret1"},
    )
    assert login_response.status_code == 200

    response = await client.get("/api/v1/admin/locations")
    assert response.status_code == 200
    data = response.json()
    assert any(c["name"] == "Bakı" for c in data["cities"])
    assert any(d["name"] == "Nərimanov" for d in data["districts"])
    assert any(m["name"] == "Gənclik" for m in data["metros"])


@pytest.mark.asyncio
async def test_admin_agent_reputation(client, auth_user, db):

    from app.models.agency import Agent

    await auth_user(email="superadmin@test.az", role="super_admin")
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": "superadmin@test.az", "password": "supersecret1"},
    )
    assert login_response.status_code == 200

    ag = Agent(
        name="Aqil Əliyev",
        email="aqil@agent.az",
        phone="+994500000003",
        verified_identity=True,
        verified_phone=True,
        member_since=None,
    )
    db.add(ag)
    await db.commit()

    response = await client.get("/api/v1/admin/agents/reputation")
    assert response.status_code == 200
    data = response.json()
    assert "formula" in data
    matches = [a for a in data["data"] if a["name"] == "Aqil Əliyev"]
    assert matches
    assert matches[0]["reputation_score"] >= 50  # base + identity + phone