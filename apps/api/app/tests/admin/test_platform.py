"""Phase 10: admin platform tests (feature flags, banners, announcements)."""

from __future__ import annotations


async def _admin(client, auth_user):
    await auth_user(email="platform-admin@test.az", role="admin")


async def test_flag_lifecycle_and_public_exposure(client, auth_user):
    await _admin(client, auth_user)

    created = await client.post(
        "/api/v1/admin/platform/flags",
        json={"key": "homepage_v2", "enabled": False, "description": "test flag"},
    )
    assert created.status_code == 201, created.text
    flag_id = created.json()["id"]
    assert created.json()["enabled"] is False

    # Disabled flags are not exposed publicly
    public = await client.get("/api/v1/public/platform/flags")
    assert public.status_code == 200
    assert "homepage_v2" not in public.json()

    updated = await client.patch(
        f"/api/v1/admin/platform/flags/{flag_id}",
        json={"enabled": True},
    )
    assert updated.status_code == 200
    assert updated.json()["enabled"] is True

    public = await client.get("/api/v1/public/platform/flags")
    assert public.json() == {"homepage_v2": True}

    deleted = await client.delete(f"/api/v1/admin/platform/flags/{flag_id}")
    assert deleted.status_code == 200
    public = await client.get("/api/v1/public/platform/flags")
    assert "homepage_v2" not in public.json()


async def test_flag_duplicate_key_rejected(client, auth_user):
    await _admin(client, auth_user)
    first = await client.post(
        "/api/v1/admin/platform/flags",
        json={"key": "dup_flag", "enabled": True},
    )
    assert first.status_code == 201
    second = await client.post(
        "/api/v1/admin/platform/flags",
        json={"key": "dup_flag", "enabled": True},
    )
    assert second.status_code == 400


async def test_flag_endpoints_require_admin(client, auth_user):
    await auth_user(email="platform-user@test.az")
    resp = await client.post(
        "/api/v1/admin/platform/flags",
        json={"key": "nope", "enabled": True},
    )
    assert resp.status_code == 403


async def test_banner_crud_and_public_listing(client, auth_user):
    await _admin(client, auth_user)

    created = await client.post(
        "/api/v1/admin/platform/banners",
        json={
            "title_az": "Payız endirimi",
            "subtitle_az": "İlk 10 elan pulsuz",
            "image_url": "https://media.test/banner.jpg",
            "link_url": "/properties",
            "cta_label_az": "Bax",
            "badge_az": "Yeni",
            "sort_order": 1,
            "active": True,
        },
    )
    assert created.status_code == 201, created.text
    banner_id = created.json()["id"]

    # Active banners appear publicly, in sort order
    public = await client.get("/api/v1/public/platform/banners")
    assert public.status_code == 200
    titles = [b["title_az"] for b in public.json()]
    assert "Payız endirimi" in titles

    updated = await client.patch(
        f"/api/v1/admin/platform/banners/{banner_id}",
        json={"active": False},
    )
    assert updated.status_code == 200
    assert updated.json()["active"] is False

    public = await client.get("/api/v1/public/platform/banners")
    assert "Payız endirimi" not in [b["title_az"] for b in public.json()]

    deleted = await client.delete(f"/api/v1/admin/platform/banners/{banner_id}")
    assert deleted.status_code == 200


async def test_announcement_broadcast_all_creates_notifications(client, auth_user):
    await auth_user(email="broadcast-user@test.az")
    await _admin(client, auth_user)

    broadcast = await client.post(
        "/api/v1/admin/platform/announcements",
        json={
            "title": "Texniki iş",
            "message": "Sayt sabah 02:00-04:00 arası bağlı olacaq.",
            "audience": "all",
        },
    )
    assert broadcast.status_code == 201, broadcast.text
    assert broadcast.json()["audience"] == "all"

    # The regular user should now see the announcement in their inbox
    await auth_user(email="broadcast-user@test.az")
    inbox = await client.get("/api/v1/notifications?limit=50")
    assert inbox.status_code == 200
    titles = [n["title"] for n in inbox.json()]
    assert "Texniki iş" in titles


async def test_announcement_audience_agents_skips_owners(client, auth_user, db):
    from sqlalchemy import select

    from app.models.notification import Notification
    from app.models.user import User

    await auth_user(email="broadcast-agent@test.az", role="agent")
    await auth_user(email="broadcast-owner@test.az", role="owner")
    await _admin(client, auth_user)

    broadcast = await client.post(
        "/api/v1/admin/platform/announcements",
        json={
            "title": "Agentlər üçün",
            "message": "Yalnız agentlərə xüsusi təklif.",
            "audience": "agents",
        },
    )
    assert broadcast.status_code == 201

    rows = (
        await db.execute(
            select(Notification, User.role)
            .join(User, Notification.user_id == User.id)
            .where(
                Notification.kind == "announcement",
                Notification.message == "Yalnız agentlərə xüsusi təklif.",
            )
        )
    ).all()
    assert rows, "expected at least one agent notification"
    for _notification, role in rows:
        assert role in ("agent", "agency_admin")
