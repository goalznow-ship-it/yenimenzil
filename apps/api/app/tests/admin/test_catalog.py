import pytest
from sqlalchemy import select

from app.models.property import PropertyFeature


@pytest.mark.asyncio
async def test_admin_features_requires_auth(client):
    response = await client.get("/api/v1/admin/catalog/features")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_admin_features_rbac(client, auth_user):
    await auth_user(email="regular@test.az", role="user")
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": "regular@test.az", "password": "supersecret1"},
    )
    assert login_response.status_code == 200
    response = await client.get("/api/v1/admin/catalog/features")
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_admin_features_list(client, auth_user, db):
    db.add(PropertyFeature(code="elevator", label_az="Lift"))
    db.add(PropertyFeature(code="pool", label_az="Hovuz"))
    await db.commit()

    await auth_user(email="moderator@test.az", role="moderator")
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": "moderator@test.az", "password": "supersecret1"},
    )
    assert login_response.status_code == 200

    response = await client.get("/api/v1/admin/catalog/features")
    assert response.status_code == 200
    data = response.json()
    codes = {f["code"] for f in data["data"]}
    assert "elevator" in codes
    assert "pool" in codes
    assert "property_types" in data


@pytest.mark.asyncio
async def test_admin_feature_create_update_delete(client, auth_user, db):
    await auth_user(email="superadmin@test.az", role="super_admin")
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": "superadmin@test.az", "password": "supersecret1"},
    )
    assert login_response.status_code == 200

    create_response = await client.post(
        "/api/v1/admin/catalog/features",
        json={"code": "gym", "label_az": "İdman zalı"},
    )
    assert create_response.status_code == 201, create_response.text
    feature_id = create_response.json()["id"]

    # Duplicate code must conflict
    dup_response = await client.post(
        "/api/v1/admin/catalog/features",
        json={"code": "gym", "label_az": "Yenə"},
    )
    assert dup_response.status_code == 409

    update_response = await client.patch(
        f"/api/v1/admin/catalog/features/{feature_id}",
        json={"label_az": "Gim"},
    )
    assert update_response.status_code == 200
    assert update_response.json()["label_az"] == "Gim"

    delete_response = await client.delete(
        f"/api/v1/admin/catalog/features/{feature_id}"
    )
    assert delete_response.status_code == 200

    result = await db.execute(
        select(PropertyFeature).where(PropertyFeature.id == feature_id)
    )
    assert result.scalar_one_or_none() is None

    # Audit trail recorded
    from app.models.admin_log import AdminActionLog

    logs = (await db.execute(select(AdminActionLog))).scalars().all()
    actions = [l.action for l in logs]
    assert "feature.create" in actions
    assert "feature.update" in actions
    assert "feature.delete" in actions
