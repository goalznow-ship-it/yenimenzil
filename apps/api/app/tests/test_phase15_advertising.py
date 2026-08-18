"""Phase 15: advertising system tests."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest


def _mock_webhook_signature(payload: bytes, secret: str = "mock-dev-secret") -> str:
    import hashlib
    import hmac

    return hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()


@pytest.mark.asyncio
async def test_ad_campaign_crud_and_states(client, auth_user, db):
    """Test full CRUD and state transitions for ad campaigns."""
    admin = await auth_user(email="ad-admin@test.az", is_verified=True)
    admin.role = "admin"
    await db.commit()

    # Create campaign
    start = datetime.now(UTC) - timedelta(hours=1)
    end = datetime.now(UTC) + timedelta(days=7)
    created = await client.post(
        "/api/v1/admin/advertising",
        json={
            "name": "Test Campaign",
            "advertiser": "Test Corporation",
            "placement": "HOME_TOP_BANNER",
            "desktop_creative_url": "https://img.test/banner.png",
            "destination_url": "https://example.com",
            "start_at": start.isoformat(),
            "end_at": end.isoformat(),
            "priority": 10,
        },
    )
    assert created.status_code == 201, created.text
    campaign = created.json()
    campaign_id = campaign["id"]
    assert campaign["state"] == "ACTIVE"  # start_at in past

    # List campaigns
    listed = (await client.get("/api/v1/admin/advertising")).json()
    assert any(c["id"] == campaign_id for c in listed)

    # Get single
    fetched = (await client.get(f"/api/v1/admin/advertising/{campaign_id}")).json()
    assert fetched["name"] == "Test Campaign"
    assert fetched["placement"] == "HOME_TOP_BANNER"

    # Update
    updated = await client.patch(
        f"/api/v1/admin/advertising/{campaign_id}",
        json={"priority": 20, "alt_text": "Updated"},
    )
    assert updated.status_code == 200
    assert updated.json()["priority"] == 20
    assert updated.json()["alt_text"] == "Updated"

    # Pause
    paused = await client.post(f"/api/v1/admin/advertising/{campaign_id}/pause")
    assert paused.status_code == 200
    assert paused.json()["state"] == "PAUSED"

    # Resume
    resumed = await client.post(f"/api/v1/admin/advertising/{campaign_id}/resume")
    assert resumed.status_code == 200
    assert resumed.json()["state"] == "ACTIVE"

    # Archive
    archived = await client.post(f"/api/v1/admin/advertising/{campaign_id}/archive")
    assert archived.status_code == 200
    assert archived.json()["state"] == "ARCHIVED"

    # Non-admin cannot access
    _ = await auth_user(email="ad-regular@test.az")
    regular_client = await _other_client(client, auth_user, "ad-regular@test.az")
    denied = await regular_client.get("/api/v1/admin/advertising")
    assert denied.status_code == 403


@pytest.mark.asyncio
async def test_ad_campaign_url_validation(client, auth_user, db):
    """Test URL scheme validation."""
    admin = await auth_user(email="ad-url@test.az", is_verified=True)
    admin.role = "admin"
    await db.commit()

    # javascript: should be rejected
    bad = await client.post(
        "/api/v1/admin/advertising",
        json={
            "name": "Bad URL",
            "advertiser": "Test Co",
            "placement": "HOME_TOP_BANNER",
            "desktop_creative_url": "https://img.test/b.png",
            "destination_url": "javascript:alert(1)",
        },
    )
    assert bad.status_code == 400

    # http:// allowed (dev)
    ok = await client.post(
        "/api/v1/admin/advertising",
        json={
            "name": "OK URL",
            "advertiser": "Test Co",
            "placement": "HOME_TOP_BANNER",
            "desktop_creative_url": "https://img.test/b.png",
            "destination_url": "http://localhost:3000/test",
        },
    )
    assert ok.status_code == 201, ok.text


@pytest.mark.asyncio
async def test_ad_delivery_and_priority(client, auth_user, db):
    """Test public ad delivery with priority selection."""
    admin = await auth_user(email="ad-deliver@test.az", is_verified=True)
    admin.role = "admin"
    await db.commit()

    # Create two campaigns same placement, different priority
    c1 = await client.post(
        "/api/v1/admin/advertising",
        json={
            "name": "Low Priority",
            "advertiser": "Advertiser A",
            "placement": "LEFT_RAIL",
            "desktop_creative_url": "https://img.test/a.png",
            "destination_url": "https://a.com",
            "priority": 5,
        },
    )
    c2 = await client.post(
        "/api/v1/admin/advertising",
        json={
            "name": "High Priority",
            "advertiser": "Advertiser B",
            "placement": "LEFT_RAIL",
            "desktop_creative_url": "https://img.test/b.png",
            "destination_url": "https://b.com",
            "priority": 20,
        },
    )
    assert c1.status_code == 201
    assert c2.status_code == 201

    # Delivery should return higher priority
    delivery = await client.get("/api/v1/ads?placement=LEFT_RAIL&device=desktop")
    assert delivery.status_code == 200, delivery.text
    ads = delivery.json()
    assert len(ads) == 1
    assert ads[0]["id"] == c2.json()["id"]

    # Different placement returns nothing if no campaign
    empty = await client.get("/api/v1/ads?placement=RIGHT_RAIL&device=desktop")
    assert empty.status_code == 200
    assert empty.json() == []


@pytest.mark.asyncio
async def test_ad_delivery_batch(client, auth_user, db):
    """Test batch ad delivery for multiple placements."""
    admin = await auth_user(email="ad-batch@test.az", is_verified=True)
    admin.role = "admin"
    await db.commit()

    await client.post(
        "/api/v1/admin/advertising",
        json={
            "name": "Home Top",
            "advertiser": "Advertiser A",
            "placement": "HOME_TOP_BANNER",
            "desktop_creative_url": "https://img.test/a.png",
            "destination_url": "https://a.com",
        },
    )
    await client.post(
        "/api/v1/admin/advertising",
        json={
            "name": "Search Inline",
            "advertiser": "Advertiser B",
            "placement": "SEARCH_INLINE_BANNER",
            "desktop_creative_url": "https://img.test/b.png",
            "destination_url": "https://b.com",
        },
    )

    # Batch request
    batch = await client.get(
        "/api/v1/ads?placements=HOME_TOP_BANNER,SEARCH_INLINE_BANNER&device=desktop"
    )
    assert batch.status_code == 200
    ads = batch.json()
    assert len(ads) == 2
    placements = {ad["placement"] for ad in ads}
    assert placements == {"HOME_TOP_BANNER", "SEARCH_INLINE_BANNER"}


@pytest.mark.asyncio
async def test_ad_impression_click_tracking(client, auth_user, db):
    """Test impression/click recording and dedup."""
    admin = await auth_user(email="ad-track@test.az", is_verified=True)
    admin.role = "admin"
    await db.commit()

    created = await client.post(
        "/api/v1/admin/advertising",
        json={
            "name": "Track Test",
            "advertiser": "Test Co",
            "placement": "MOBILE_TOP",
            "desktop_creative_url": "https://img.test/m.png",
            "destination_url": "https://test.com",
        },
    )
    campaign_id = created.json()["id"]

    # Impression
    impr = await client.post(
        f"/api/v1/ads/{campaign_id}/impression",
        json={"session_key": "sess-123"},
    )
    assert impr.status_code == 200

    # Click
    clk = await client.post(
        f"/api/v1/ads/{campaign_id}/click",
        json={"session_key": "sess-123"},
    )
    assert clk.status_code == 200

    # Verify counters
    stats = (await client.get(f"/api/v1/admin/advertising/{campaign_id}/stats")).json()
    assert stats["total_impressions"] >= 1
    assert stats["total_clicks"] >= 1

    # Dedup: same session_key within window should not increment
    impr2 = await client.post(
        f"/api/v1/ads/{campaign_id}/impression",
        json={"session_key": "sess-123"},
    )
    assert impr2.status_code == 200
    stats2 = (await client.get(f"/api/v1/admin/advertising/{campaign_id}/stats")).json()
    assert stats2["total_impressions"] == stats["total_impressions"]


@pytest.mark.asyncio
async def test_ad_device_targeting(client, auth_user, db):
    """Test device targeting filter in delivery."""
    admin = await auth_user(email="ad-device@test.az", is_verified=True)
    admin.role = "admin"
    await db.commit()

    # Desktop-only campaign
    await client.post(
        "/api/v1/admin/advertising",
        json={
            "name": "Desktop Only",
            "advertiser": "Advertiser A",
            "placement": "LEFT_RAIL",
            "desktop_creative_url": "https://img.test/a.png",
            "destination_url": "https://a.com",
            "device_targeting": "desktop",
        },
    )
    # Mobile-only campaign
    await client.post(
        "/api/v1/admin/advertising",
        json={
            "name": "Mobile Only",
            "advertiser": "Advertiser B",
            "placement": "LEFT_RAIL",
            "mobile_creative_url": "https://img.test/b.png",
            "destination_url": "https://b.com",
            "device_targeting": "mobile",
        },
    )

    # Desktop request returns desktop campaign
    desk = await client.get("/api/v1/ads?placement=LEFT_RAIL&device=desktop")
    assert desk.status_code == 200
    assert len(desk.json()) == 1
    assert (
        desk.json()[0]["id"]
        == (await client.get("/api/v1/admin/advertising?search=Desktop")).json()[0][
            "id"
        ]
    )

    # Mobile request returns mobile campaign
    mob = await client.get("/api/v1/ads?placement=LEFT_RAIL&device=mobile")
    assert mob.status_code == 200
    assert len(mob.json()) == 1
    assert (
        mob.json()[0]["id"]
        == (await client.get("/api/v1/admin/advertising?search=Mobile")).json()[0]["id"]
    )


@pytest.mark.asyncio
async def test_ad_overview_stats(client, auth_user, db):
    """Test advertising overview stats endpoint."""
    admin = await auth_user(email="ad-stats@test.az", is_verified=True)
    admin.role = "admin"
    await db.commit()

    await client.post(
        "/api/v1/admin/advertising",
        json={
            "name": "Stats Test",
            "advertiser": "Test Co",
            "placement": "HOME_TOP_BANNER",
            "desktop_creative_url": "https://img.test/s.png",
            "destination_url": "https://test.com",
        },
    )

    resp = await client.get("/api/v1/admin/advertising/overview/stats")
    print("OVERVIEW STATUS:", resp.status_code)
    print("OVERVIEW RESPONSE:", resp.text)
    overview = resp.json()
    assert overview["total_impressions"] >= 0
    assert overview["total_clicks"] >= 0
    assert "daily_trend" in overview
    assert "top_campaign" in overview
    assert "top_placement" in overview


async def _other_client(client, auth_user, email):
    from app.tests.test_phase7_marketplace import _create_authenticated_client

    return await _create_authenticated_client(auth_user, email)


@pytest.mark.asyncio
async def test_ad_campaign_state_expiration(client, auth_user, db):
    """Test campaign state changes based on dates."""
    admin = await auth_user(email="ad-expire@test.az", is_verified=True)
    admin.role = "admin"
    await db.commit()

    # Past end date -> EXPIRED
    past = await client.post(
        "/api/v1/admin/advertising",
        json={
            "name": "Expired",
            "advertiser": "Advertiser A",
            "placement": "HOME_TOP_BANNER",
            "desktop_creative_url": "https://img.test/e.png",
            "destination_url": "https://a.com",
            "end_at": (datetime.now(UTC) - timedelta(days=1)).isoformat(),
        },
    )
    assert past.json()["state"] == "EXPIRED"

    # Future start -> SCHEDULED
    future = await client.post(
        "/api/v1/admin/advertising",
        json={
            "name": "Future",
            "advertiser": "Advertiser B",
            "placement": "HOME_TOP_BANNER",
            "desktop_creative_url": "https://img.test/f.png",
            "destination_url": "https://b.com",
            "start_at": (datetime.now(UTC) + timedelta(days=1)).isoformat(),
        },
    )
    assert future.json()["state"] == "SCHEDULED"
