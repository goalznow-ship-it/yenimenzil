import pytest
from sqlalchemy import select

from app.models.admin_log import AdminActionLog
from app.tests.conftest import make_property_payload


@pytest.mark.asyncio
async def test_admin_audit_requires_auth(client):
    response = await client.get("/api/v1/admin/audit-logs")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_admin_audit_requires_admin_role(client, auth_user):
    await auth_user(email="regular@test.az", role="user")
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": "regular@test.az", "password": "supersecret1"},
    )
    assert login_response.status_code == 200
    response = await client.get("/api/v1/admin/audit-logs")
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_admin_audit_records_user_update(client, auth_user, db):
    """A senior admin role change must be captured in the audit log."""
    await auth_user(email="superadmin@test.az", role="super_admin")
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": "superadmin@test.az", "password": "supersecret1"},
    )
    assert login_response.status_code == 200

    target = await auth_user(email="victim@test.az", role="user")

    # Re-login as super admin to override the cookies set by auth_user for target
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": "superadmin@test.az", "password": "supersecret1"},
    )
    assert login_response.status_code == 200

    response = await client.patch(
        f"/api/v1/admin/users/{target.id}",
        json={"role": "moderator"},
    )
    assert response.status_code == 200

    result = await db.execute(
        select(AdminActionLog).where(AdminActionLog.entity_id == target.id)
    )
    log = result.scalar_one()
    assert log.entity_type == "user"
    assert log.admin_id is not None


@pytest.mark.asyncio
async def test_admin_audit_endpoint_returns_feed(client, auth_user, db):

    from app.models.enums import ModerationAction
    from app.models.moderation import ModerationLog

    await auth_user(email="superadmin@test.az", role="super_admin")
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": "superadmin@test.az", "password": "supersecret1"},
    )
    assert login_response.status_code == 200

    mod_user = await auth_user(email="mod@test.az", role="moderator")

    # Create a property through the API as an owner so a row exists
    owner = await auth_user(email="owner@test.az", role="owner")
    create_response = await client.post(
        "/api/v1/properties",
        json=make_property_payload(owner.id),
    )
    assert create_response.status_code == 201, create_response.text
    prop_id = create_response.json()["id"]

    db.add(
        ModerationLog(
            property_id=prop_id,
            moderator_id=mod_user.id,
            action=ModerationAction.APPROVED,
            reason="looks good",
        )
    )
    await db.commit()

    # Re-login as super admin to override the cookies set by auth_user for owner
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": "superadmin@test.az", "password": "supersecret1"},
    )
    assert login_response.status_code == 200

    response = await client.get("/api/v1/admin/audit-logs")
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert "pagination" in data
    moderation_entries = [e for e in data["data"] if e["source"] == "moderation"]
    assert any(e["action"] == "moderation.approved" for e in moderation_entries)


@pytest.mark.asyncio
async def test_admin_audit_pagination(client, auth_user):
    await auth_user(email="superadmin@test.az", role="super_admin")
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": "superadmin@test.az", "password": "supersecret1"},
    )
    assert login_response.status_code == 200
    response = await client.get("/api/v1/admin/audit-logs?limit=1")
    assert response.status_code == 200
    data = response.json()
    assert data["pagination"]["limit"] == 1
    assert len(data["data"]) <= 1