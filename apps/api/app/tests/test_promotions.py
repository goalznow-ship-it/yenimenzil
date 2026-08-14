"""Phase 10: listing monetization tests (promotion products)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest


@pytest.fixture()
async def promotion_products(db):
    """Seed the default promotion products (mirrors the migration seed)."""
    from app.models.promotion import PromotionProduct

    specs = [
        ("standard", "Standart", 500, 7, False),
        ("premium", "Premium", 1500, 14, True),
        ("vip", "VIP", 3000, 30, True),
        ("top", "Top", 5000, 30, True),
        ("urgent", "Təcili", 7000, 7, False),
    ]
    products = [
        PromotionProduct(
            code=code,
            label_az=label,
            description_az="test",
            price=price,
            duration_days=days,
            sort_order=i,
            is_premium_tier=premium,
            enabled=True,
        )
        for i, (code, label, price, days, premium) in enumerate(specs, start=1)
    ]
    db.add_all(products)
    await db.commit()
    return {p.code: p for p in products}


@pytest.fixture()
async def funded_seller(client, auth_user, db):
    """A user with wallet balance to buy promotions."""
    user = await auth_user(email="promo@test.az", is_verified=True)

    from app.models.wallet import Wallet

    db.add(Wallet(user_id=user.id, balance=100_000))
    await db.commit()
    return {"user": user}


@pytest.fixture()
async def active_listing(client, funded_seller, feature_catalog):
    from app.tests.conftest import make_property_payload

    payload = make_property_payload(funded_seller["user"].id)
    resp = await client.post("/api/v1/properties", json=payload)
    assert resp.status_code == 201, resp.text
    submitted = await client.post(f"/api/v1/properties/{resp.json()['id']}/submit")
    assert submitted.status_code == 200, submitted.text
    return submitted.json()


async def test_catalog_returns_enabled_products(
    client, funded_seller, promotion_products
):
    resp = await client.get("/api/v1/wallet/promotions/catalog")
    assert resp.status_code == 200
    tiers = [item["tier"] for item in resp.json()]
    assert set(tiers) == {"standard", "premium", "vip", "top", "urgent"}
    vip = next(item for item in resp.json() if item["tier"] == "vip")
    assert vip["price"] == 3000
    assert vip["days"] == 30


async def test_purchase_debits_wallet_and_sets_flags(
    client, funded_seller, promotion_products, active_listing
):
    resp = await client.post(
        "/api/v1/wallet/promotions",
        json={"property_id": active_listing["id"], "tier": "vip"},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["promotion_status"] == "active"
    assert data["transaction"]["amount"] == -3000
    assert data["purchase_id"] is not None
    assert data["expires_at"] is not None
    assert datetime.fromisoformat(data["expires_at"]) > datetime.now(UTC)

    wallet = (await client.get("/api/v1/wallet")).json()
    assert wallet["balance"] == 100_000 - 3000


async def test_purchase_insufficient_balance(client, auth_user, promotion_products):
    user = await auth_user(email="poor@test.az", is_verified=True)

    from app.tests.conftest import make_property_payload

    payload = make_property_payload(user.id)
    created = await client.post("/api/v1/properties", json=payload)
    assert created.status_code == 201, created.text
    submitted = await client.post(f"/api/v1/properties/{created.json()['id']}/submit")
    assert submitted.status_code == 200, submitted.text

    resp = await client.post(
        "/api/v1/wallet/promotions",
        json={"property_id": created.json()["id"], "tier": "premium"},
    )
    assert resp.status_code == 402


async def test_disabled_product_cannot_be_purchased(
    client, funded_seller, promotion_products, active_listing
):
    from app.db.session import async_session_factory
    from app.models.promotion import PromotionProduct

    async with async_session_factory() as db:
        product = await db.get(PromotionProduct, promotion_products["urgent"].id)
        product.enabled = False
        await db.commit()

    resp = await client.post(
        "/api/v1/wallet/promotions",
        json={"property_id": active_listing["id"], "tier": "urgent"},
    )
    assert resp.status_code == 400
    assert "disabled" in resp.json()["detail"]

    catalog = (await client.get("/api/v1/wallet/promotions/catalog")).json()
    assert "urgent" not in [item["tier"] for item in catalog]


async def test_my_promotions_lists_purchases(
    client, funded_seller, promotion_products, active_listing
):
    await client.post(
        "/api/v1/wallet/promotions",
        json={"property_id": active_listing["id"], "tier": "standard"},
    )
    resp = await client.get("/api/v1/wallet/promotions")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["tier"] == "standard"
    assert data[0]["status"] == "active"
    assert data[0]["property_id"] == active_listing["id"]


async def test_expiry_watcher_clears_expired_promotions(
    client, funded_seller, promotion_products, active_listing
):
    await client.post(
        "/api/v1/wallet/promotions",
        json={"property_id": active_listing["id"], "tier": "standard"},
    )

    from sqlalchemy import update

    from app.db.session import async_session_factory
    from app.models.property import Property
    from app.services.expiry_watcher import _check_expiring_promotions

    async with async_session_factory() as session:
        await session.execute(
            update(Property)
            .where(Property.id == active_listing["id"])
            .values(promotion_expires_at=datetime.now(UTC) - timedelta(days=1))
        )
        await session.commit()

    await _check_expiring_promotions()

    detail = await client.get(f"/api/v1/properties/{active_listing['id']}")
    assert detail.status_code == 200
    body = detail.json()
    assert body["is_promoted"] is False
    assert body["promotion_tier"] is None

    my = (await client.get("/api/v1/wallet/promotions")).json()
    assert my[0]["status"] == "expired"


async def test_admin_updates_product_price(client, auth_user, promotion_products):
    await auth_user(email="adminx@test.az", role="admin")

    pid = str(promotion_products["vip"].id)
    resp = await client.patch(
        f"/api/v1/admin/promotions/products/{pid}",
        json={"price": 3500, "enabled": False},
    )
    assert resp.status_code == 200
    assert resp.json()["price"] == 3500
    assert resp.json()["enabled"] is False


async def test_admin_create_product(client, auth_user):
    await auth_user(email="adminy@test.az", role="admin")

    resp = await client.post(
        "/api/v1/admin/promotions/products",
        json={
            "code": "homepage",
            "label_az": "Ana səhifə",
            "price": 9000,
            "duration_days": 30,
            "is_premium_tier": True,
        },
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["code"] == "homepage"

    dup = await client.post(
        "/api/v1/admin/promotions/products",
        json={"code": "homepage", "label_az": "Dup", "price": 1, "duration_days": 1},
    )
    assert dup.status_code == 400
