"""Phase 11: regression tests for launch-readiness fixes.

Covers: media validator resolution rejection, analytics event validation,
price history access control, duplicate active promotion, saved-search alerts.
"""

from __future__ import annotations

import io

import pytest
from PIL import Image


def _png_bytes(width: int = 800, height: int = 600) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (width, height), (120, 140, 200)).save(buf, format="PNG")
    return buf.getvalue()


async def _make_property(client, user_id: str, *, status: str = "draft"):
    from app.tests.conftest import make_property_payload

    payload = make_property_payload(user_id, status="draft", media=[])
    resp = await client.post("/api/v1/properties", json=payload)
    assert resp.status_code == 201, resp.text
    created = resp.json()
    if status == "active":
        resp = await client.post(f"/api/v1/properties/{created['id']}/submit")
        assert resp.status_code == 200, resp.text
    return created


@pytest.fixture()
async def promotion_products(db):
    from app.models.promotion import PromotionProduct

    specs = [
        ("standard", "Standart", 1000, 30, False),
        ("premium", "Premium", 2000, 30, False),
        ("vip", "VIP", 3000, 30, True),
        ("top", "Top", 5000, 14, True),
        ("urgent", "Təcili", 700, 7, False),
    ]
    products = [
        PromotionProduct(
            code=code,
            label_az=label,
            price=price,
            duration_days=days,
            is_premium_tier=premium,
            enabled=True,
        )
        for code, label, price, days, premium in specs
    ]
    db.add_all(products)
    await db.commit()
    return {p.code: p for p in products}


@pytest.fixture()
async def funded_seller(client, auth_user, db):
    """A user with wallet balance to buy promotions."""
    user = await auth_user(email="promo11@test.az", is_verified=True)

    from app.models.wallet import Wallet

    db.add(Wallet(user_id=user.id, balance=100_000))
    await db.commit()
    return {"user": user}


@pytest.fixture()
async def active_listing(client, funded_seller, feature_catalog):
    return await _make_property(client, str(funded_seller["user"].id), status="active")


@pytest.fixture()
async def seller(client, auth_user):
    user = await auth_user(email="media11@test.az", is_verified=True)
    return {"user": user}


@pytest.fixture()
async def listing(client, seller, feature_catalog):
    return await _make_property(client, str(seller["user"].id))


# ---------------------------------------------------------------------------
# Media validator
# ---------------------------------------------------------------------------


async def test_media_validator_resolution_logic():
    from app.services.media_validator import validate_image_file

    ok, error = validate_image_file(_png_bytes(800, 600), "large.png")
    assert ok is True
    assert error is None

    ok, error = validate_image_file(_png_bytes(300, 300), "small.png")
    assert ok is False
    assert error is not None
    assert "Resolution too small" in error


async def test_media_upload_rejects_small_resolution(
    client, auth_user, seller, listing, monkeypatch
):
    """End-to-end: tiny image must be rejected at the API, not crash (1-tuple bug)."""
    import app.api.v1.endpoints.properties as properties_module

    async def _fake_upload(_data, _key, content_type, metadata):
        return {"url": f"https://minio.test/{content_type}/{len(_data)}", **metadata}

    monkeypatch.setattr(properties_module, "upload_file", _fake_upload)

    resp = await client.post(
        f"/api/v1/properties/{listing['id']}/media",
        files={"files": ("small.png", _png_bytes(300, 300), "image/png")},
    )
    assert resp.status_code == 400, resp.text
    assert "Resolution too small" in resp.json()["detail"]


# ---------------------------------------------------------------------------
# Analytics event validation
# ---------------------------------------------------------------------------


async def test_analytics_event_invalid_type_returns_422(client, auth_user):
    await auth_user(email="analytics-bad@test.az")

    resp = await client.post(
        "/api/v1/analytics/events",
        json={"event_type": "UPPERCASE_EVENT", "payload": {}},
    )
    assert resp.status_code == 422, resp.text

    resp = await client.post(
        "/api/v1/analytics/events",
        json={"event_type": "search", "payload": {"query": "mənzil"}},
    )
    assert resp.status_code == 201, resp.text


# ---------------------------------------------------------------------------
# Price history access control
# ---------------------------------------------------------------------------


async def test_price_history_requires_owner_or_staff(client, auth_user, db):
    owner = await auth_user(email="ph-owner@test.az", is_verified=True)
    created = await _make_property(client, str(owner.id))
    await db.commit()

    await auth_user(email="ph-other@test.az")
    resp = await client.get(f"/api/v1/price-history/{created['id']}")
    assert resp.status_code == 403, resp.text

    await auth_user(email="ph-owner@test.az")
    resp = await client.get(f"/api/v1/price-history/{created['id']}")
    assert resp.status_code == 200, resp.text


# ---------------------------------------------------------------------------
# Duplicate active promotion
# ---------------------------------------------------------------------------


async def test_duplicate_active_promotion_returns_409(
    client, funded_seller, promotion_products, active_listing
):
    first = await client.post(
        "/api/v1/wallet/promotions",
        json={"property_id": active_listing["id"], "tier": "vip"},
    )
    assert first.status_code == 200, first.text

    second = await client.post(
        "/api/v1/wallet/promotions",
        json={"property_id": active_listing["id"], "tier": "vip"},
    )
    assert second.status_code == 409, second.text


async def test_concurrent_same_promotion_purchase_serializes(
    client, funded_seller, promotion_products, active_listing
):
    """Two simultaneous purchases of the same product must yield exactly one
    active purchase: one 200 and one 409 (wallet row lock + partial unique
    index).
    """
    import asyncio

    payload = {"property_id": active_listing["id"], "tier": "premium"}
    first, second = await asyncio.gather(
        client.post("/api/v1/wallet/promotions", json=payload),
        client.post("/api/v1/wallet/promotions", json=payload),
    )
    codes = sorted([first.status_code, second.status_code])
    assert codes == [200, 409], f"expected [200, 409], got {codes}"

    wallet = (await client.get("/api/v1/wallet")).json()
    # only one VIP purchase debited
    assert wallet["balance"] == 100_000 - 2000

    mine = (await client.get("/api/v1/wallet/promotions")).json()
    active = [p for p in mine if p["status"] == "active"]
    assert len(active) == 1


# ---------------------------------------------------------------------------
# Saved-search alerts
# ---------------------------------------------------------------------------


async def test_saved_search_alerts_notifies_matching_listings(
    client, auth_user, db, feature_catalog
):
    from datetime import UTC, datetime, timedelta

    from sqlalchemy import select

    from app.models.notification import Notification
    from app.models.property import Property, PropertyStatus
    from app.models.saved_search import SavedSearch
    from app.services.expiry_watcher import _run_saved_search_alerts

    user = await auth_user(email="alerts@test.az", is_verified=True)

    now = datetime.now(UTC)
    matching = await _make_property(client, str(user.id), status="active")
    prop = await db.get(Property, matching["id"])
    prop.status = PropertyStatus.ACTIVE.value
    prop.published_at = now - timedelta(hours=2)
    prop.deal_type = "sale"
    prop.property_type = "apartment"

    db.add(prop)
    await db.commit()

    db.add(
        SavedSearch(
            user_id=user.id,
            name="Yeni mənzillər",
            filters={"deal_type": "sale", "property_type": "apartment"},
            is_active=True,
        )
    )
    await db.commit()

    ran = await _run_saved_search_alerts()
    assert ran is True
    ran_again = await _run_saved_search_alerts()
    assert ran_again is False

    notifications = (
        (
            await db.execute(
                select(Notification).where(Notification.kind == "saved_search")
            )
        )
        .scalars()
        .all()
    )
    assert len(notifications) >= 1
    assert "yeni elan" in notifications[-1].title
