import pytest


async def _superadmin_login(client, auth_user):
    await auth_user(email="superadmin@test.az", role="super_admin")
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": "superadmin@test.az", "password": "supersecret1"},
    )
    assert login_response.status_code == 200


@pytest.mark.asyncio
async def test_admin_promotions_requires_auth(client):
    response = await client.get("/api/v1/admin/promotions/listings")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_admin_promotions_rbac(client, auth_user):
    """Moderators cannot manage promotions (admin/super_admin only)."""
    await auth_user(email="moderator@test.az", role="moderator")
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": "moderator@test.az", "password": "supersecret1"},
    )
    assert login_response.status_code == 200
    response = await client.get("/api/v1/admin/promotions/listings")
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_admin_promotion_activate_deactivate(client, auth_user, db):
    from app.tests.conftest import make_property_payload

    await _superadmin_login(client, auth_user)

    owner = await auth_user(email="owner@test.az", role="owner")
    create_response = await client.post(
        "/api/v1/properties",
        json=make_property_payload(owner.id),
    )
    assert create_response.status_code == 201, create_response.text
    prop_id = create_response.json()["id"]

    # Re-login as super admin to override the cookies set by auth_user for owner
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": "superadmin@test.az", "password": "supersecret1"},
    )
    assert login_response.status_code == 200

    activate_response = await client.post(
        f"/api/v1/admin/promotions/listings/{prop_id}/activate",
        json={"tier": "vip", "days": 10},
    )
    assert activate_response.status_code == 200, activate_response.text
    data = activate_response.json()
    assert data["tier"] == "vip"

    listing_response = await client.get("/api/v1/admin/promotions/listings")
    assert listing_response.status_code == 200
    promoted = [l for l in listing_response.json()["data"] if l["id"] == prop_id]
    assert promoted, listing_response.text
    assert promoted[0]["is_promoted"] is True
    assert promoted[0]["promotion_status"] == "active"
    assert "products" in listing_response.json()

    deactivate_response = await client.post(
        f"/api/v1/admin/promotions/listings/{prop_id}/deactivate"
    )
    assert deactivate_response.status_code == 200

    listing_response = await client.get("/api/v1/admin/promotions/listings")
    promoted = [l for l in listing_response.json()["data"] if l["id"] == prop_id]
    assert promoted[0]["is_promoted"] is False
    assert promoted[0]["promotion_status"] == "none"


@pytest.mark.asyncio
async def test_admin_promotion_activation_logs_audit(client, auth_user, db):
    from sqlalchemy import select

    from app.models.admin_log import AdminActionLog

    await _superadmin_login(client, auth_user)
    owner = await auth_user(email="owner@test.az", role="owner")
    from app.tests.conftest import make_property_payload

    create_response = await client.post(
        "/api/v1/properties",
        json=make_property_payload(owner.id),
    )
    prop_id = create_response.json()["id"]

    # Re-login as super admin to override the cookies set by auth_user for owner
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": "superadmin@test.az", "password": "supersecret1"},
    )
    assert login_response.status_code == 200

    activate_response = await client.post(
        f"/api/v1/admin/promotions/listings/{prop_id}/activate",
        json={"tier": "urgent"},
    )
    assert activate_response.status_code == 200, activate_response.text
    logs = (await db.execute(select(AdminActionLog))).scalars().all()
    assert any(l.action == "promotion.activate" for l in logs)
