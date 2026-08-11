import pytest

from app.tests.conftest import make_property_payload


async def _create(client, user, **overrides):
    payload = make_property_payload(user.id, **overrides)
    response = await client.post("/api/v1/properties", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


@pytest.mark.asyncio
async def test_create_defaults_to_draft(client, auth_user, feature_catalog):
    owner = await auth_user()
    body = await _create(client, owner)
    assert body["status"] == "draft"
    assert body["published_at"] is None


@pytest.mark.asyncio
async def test_submit_draft_goes_to_pending_review(client, auth_user, feature_catalog):
    owner = await auth_user()
    created = await _create(client, owner)
    response = await client.post(f"/api/v1/properties/{created['id']}/submit")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "pending_review"
    assert body["published_at"] is None


@pytest.mark.asyncio
async def test_submit_draft_auto_publishes_verified_user(
    client, auth_user, feature_catalog
):
    owner = await auth_user(is_verified=True)
    created = await _create(client, owner)
    response = await client.post(f"/api/v1/properties/{created['id']}/submit")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "active"
    assert body["published_at"] is not None


@pytest.mark.asyncio
async def test_submit_draft_auto_publishes_agent(client, auth_user, feature_catalog):
    owner = await auth_user(role="agent")
    created = await _create(client, owner)
    response = await client.post(f"/api/v1/properties/{created['id']}/submit")
    assert response.status_code == 200
    assert response.json()["status"] == "active"


@pytest.mark.asyncio
async def test_submit_active_listing_rejected(client, auth_user, feature_catalog):
    owner = await auth_user(role="moderator")
    created = await _create(client, owner, status="active")
    response = await client.post(f"/api/v1/properties/{created['id']}/submit")
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_submit_rejected_listing_goes_back_to_pending(
    client, auth_user, feature_catalog
):
    owner = await auth_user()
    created = await _create(client, owner)
    await client.post(f"/api/v1/properties/{created['id']}/submit")
    assert created["status"] == "draft"

    moderator = await auth_user(email="mod@test.az", role="moderator")
    # moderator rejects the listing via PATCH (staff bypasses status guard)
    response = await client.patch(
        f"/api/v1/properties/{created['id']}", json={"status": "rejected"}
    )
    assert response.status_code == 200
    assert response.json()["status"] == "rejected"
    assert moderator.role == "moderator"

    # owner re-submits the rejected listing
    await auth_user(email=owner.email)
    response = await client.post(f"/api/v1/properties/{created['id']}/submit")
    assert response.status_code == 200
    assert response.json()["status"] == "pending_review"


@pytest.mark.asyncio
async def test_submit_other_users_listing_rejected(
    client, auth_user, feature_catalog
):
    owner = await auth_user()
    created = await _create(client, owner)
    await auth_user(email="other@test.az")
    response = await client.post(f"/api/v1/properties/{created['id']}/submit")
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_submit_requires_auth(client, feature_catalog):
    response = await client.post(
        f"/api/v1/properties/{'00000000-0000-0000-0000-000000000000'}/submit"
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_owner_cannot_set_active_via_patch(client, auth_user, feature_catalog):
    owner = await auth_user()
    created = await _create(client, owner)
    response = await client.patch(
        f"/api/v1/properties/{created['id']}", json={"status": "active"}
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_owner_can_archive_or_mark_sold(client, auth_user, feature_catalog):
    owner = await auth_user()
    created = await _create(client, owner)

    response = await client.patch(
        f"/api/v1/properties/{created['id']}", json={"status": "archived"}
    )
    assert response.status_code == 200
    assert response.json()["status"] == "archived"

    response = await client.patch(
        f"/api/v1/properties/{created['id']}", json={"status": "sold"}
    )
    assert response.status_code == 200
    assert response.json()["status"] == "sold"


@pytest.mark.asyncio
async def test_mine_lists_own_properties_across_statuses(
    client, auth_user, feature_catalog
):
    owner = await auth_user()
    created = await _create(client, owner)
    await _create(client, owner, title="İkinci elan")

    response = await client.get("/api/v1/properties/mine")
    assert response.status_code == 200
    items = response.json()
    assert len(items) == 2
    assert {i["id"] for i in items} == {created["id"], items[0]["id"]}

    response = await client.get("/api/v1/properties/mine?status=draft")
    assert response.status_code == 200
    assert len(response.json()) == 2

    await client.patch(
        f"/api/v1/properties/{created['id']}", json={"status": "archived"}
    )
    response = await client.get("/api/v1/properties/mine?status=archived")
    assert len(response.json()) == 1
    response = await client.get("/api/v1/properties/mine?status=draft")
    assert len(response.json()) == 1


@pytest.mark.asyncio
async def test_mine_requires_auth(client):
    response = await client.get("/api/v1/properties/mine")
    assert response.status_code == 401
