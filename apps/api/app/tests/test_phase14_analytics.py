"""Phase 14: advanced analytics (conversion, trend, agency analytics, search events)."""

from __future__ import annotations

import pytest

from app.models.analytics import AnalyticsEvent
from app.models.enums import AnalyticsEventType


async def _create_listing_with_events(client, auth_user, db):
    from app.tests.conftest import make_property_payload

    user = await auth_user(email="analytics-owner@test.az", is_verified=True)
    payload = make_property_payload(str(user.id), status="draft", media=[])
    created = await client.post("/api/v1/properties", json=payload)
    assert created.status_code == 201, created.text
    prop_id = created.json()["id"]

    db.add_all(
        [
            AnalyticsEvent(
                user_id=user.id,
                property_id=prop_id,
                event_type="property_view",
                payload={"source": "detail"},
            )
            for _ in range(10)
        ]
    )
    db.add_all(
        [
            AnalyticsEvent(
                user_id=user.id,
                property_id=prop_id,
                event_type="phone_reveal",
                payload={},
            )
            for _ in range(2)
        ]
    )
    db.add(
        AnalyticsEvent(
            user_id=user.id,
            property_id=prop_id,
            event_type="whatsapp_click",
            payload={},
        )
    )
    await db.commit()
    return user, prop_id


@pytest.mark.asyncio
async def test_listing_analytics_conversion_and_trend(
    client, auth_user, db, feature_catalog
):
    user, prop_id = await _create_listing_with_events(client, auth_user, db)
    del user

    response = await client.get(f"/api/v1/properties/{prop_id}/analytics?days=30")
    assert response.status_code == 200, response.text
    data = response.json()

    assert data["period_views"] == 10
    assert data["phone_reveals"] == 2
    assert data["whatsapp_clicks"] == 1
    assert data["days"] == 30
    assert len(data["trend"]) == 30
    today = data["trend"][-1]
    assert today["views"] == 10
    assert today["phone_reveals"] == 2
    assert data["conversion"]["phone_rate"] == 20.0
    assert data["conversion"]["favorite_rate"] == 0.0

    # unauthorized owner cannot see someone else's analytics
    other_client = await _other_client(client, auth_user, "analytics-other@test.az")
    denied = await other_client.get(f"/api/v1/properties/{prop_id}/analytics")
    assert denied.status_code in (403, 404)


async def _other_client(client, auth_user, email):
    from app.tests.test_phase7_marketplace import _create_authenticated_client

    return await _create_authenticated_client(auth_user, email)


@pytest.mark.asyncio
async def test_search_logs_analytics_event(client, auth_user, db):
    await auth_user(email="search-analytics@test.az")
    response = await client.get(
        "/api/v1/properties?city=Bakı&district=Nəsimi&property_type=apartment&deal=sale"
    )
    assert response.status_code == 200

    events = (
        (
            await db.execute(
                (
                    __import__("sqlalchemy")
                    .select(AnalyticsEvent)
                    .where(AnalyticsEvent.event_type == AnalyticsEventType.SEARCH.value)
                ).order_by(AnalyticsEvent.created_at.desc())
            )
        )
        .scalars()
        .all()
    )
    assert events, "no search event logged"
    latest = events[0]
    assert "Bakı" in latest.payload["query"]
    assert latest.payload["price_min"] is None


@pytest.mark.asyncio
async def test_agency_analytics_endpoint(client, auth_user, db):
    from app.models.agency import Agency, Agent
    from app.models.enums import UserRole

    admin = await auth_user(email="agency-admin@test.az", is_verified=True)
    agency = Agency(name="Test Agentlik", slug="test-agentlik")
    db.add(agency)
    await db.flush()
    db.add(
        Agent(
            user_id=admin.id,
            agency_id=agency.id,
            name="Admin Agent",
            email="agency-admin@test.az",
        )
    )
    admin.role = UserRole.AGENCY_ADMIN
    await db.commit()

    response = await client.get("/api/v1/agencies/me/analytics?days=30")
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["agency_id"] == str(agency.id)
    assert data["agency_name"] == "Test Agentlik"
    assert data["days"] == 30
    assert data["listings_count"] == 0
    assert data["total_leads"] == 0


@pytest.mark.asyncio
async def test_agency_analytics_denied_for_regular_user(client, auth_user):
    await auth_user(email="plain-user@test.az")
    response = await client.get("/api/v1/agencies/me/analytics")
    assert response.status_code == 403
