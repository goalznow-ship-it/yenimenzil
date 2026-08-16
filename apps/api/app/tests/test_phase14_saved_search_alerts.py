"""Phase 14: saved-search email alerts (digest, dedup, unsubscribe)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select

from app.models.notification import Notification
from app.models.property import Property, PropertyStatus
from app.models.saved_search import SavedSearch


async def _clear_throttle():
    import redis.asyncio as aioredis

    from app.core.config import get_settings
    from app.services import expiry_watcher, saved_search_alerts

    expiry_watcher._last_alert_run = None
    saved_search_alerts._last_alert_run = None
    try:
        client = aioredis.from_url(
            get_settings().REDIS_URL, socket_connect_timeout=1, socket_timeout=1
        )
        await client.delete("saved_search_alerts:last_run")
        await client.aclose()
    except Exception:  # noqa: BLE001, S110 - best-effort throttle reset
        pass


async def _make_active_property(client, user_id, db, title="Digest test"):
    from app.tests.conftest import make_property_payload

    payload = make_property_payload(user_id, status="draft", media=[])
    resp = await client.post("/api/v1/properties", json=payload)
    assert resp.status_code == 201, resp.text
    prop = await db.get(Property, resp.json()["id"])
    prop.status = PropertyStatus.ACTIVE.value
    prop.published_at = datetime.now(UTC) - timedelta(hours=2)
    prop.title = title
    await db.commit()
    return prop


@pytest.mark.asyncio
async def test_digest_creates_notification_and_email(
    client, auth_user, db, feature_catalog, monkeypatch
):
    from app.services.saved_search_alerts import _run_saved_search_alerts

    await _clear_throttle()
    user = await auth_user(email="digest1@test.az", is_verified=True)
    prop = await _make_active_property(client, str(user.id), db, "Digest elanı")

    db.add(
        SavedSearch(
            user_id=user.id,
            name="Mənzillər",
            filters={"deal_type": "sale", "property_type": "apartment"},
            is_active=True,
            email_enabled=True,
        )
    )
    await db.commit()

    sent: list[tuple] = []

    def spy_email(to, subject, text_body, *, html_body=None):
        sent.append((to, subject, text_body, html_body))

    monkeypatch.setattr("app.services.saved_search_alerts.send_email", spy_email)

    ran = await _run_saved_search_alerts()
    assert ran is True

    # In-app notification created with dedup payload
    notifications = (
        (
            await db.execute(
                select(Notification).where(
                    Notification.kind == "saved_search",
                    Notification.user_id == user.id,
                )
            )
        )
        .scalars()
        .all()
    )
    assert len(notifications) == 1
    payload = notifications[0].payload
    assert payload["search_id"]
    assert str(prop.id) in payload["property_ids"]

    # Email digest sent once, contains listing + unsubscribe link
    assert len(sent) == 1
    to, subject, text, _ = sent[0]
    assert to == user.email
    assert "yeni elan" in subject
    assert prop.title in text
    assert "/saved-searches/unsubscribe" in text
    assert "İmtina" in text
    assert f"/property/{prop.id}" in text


@pytest.mark.asyncio
async def test_digest_deduplicates_notifications(
    client, auth_user, db, feature_catalog
):
    from app.services.saved_search_alerts import _run_saved_search_alerts

    await _clear_throttle()
    user = await auth_user(email="digest2@test.az", is_verified=True)
    await _make_active_property(client, str(user.id), db, "Dedup elanı")

    db.add(
        SavedSearch(
            user_id=user.id,
            name="Dedup",
            filters={"deal_type": "sale", "property_type": "apartment"},
            is_active=True,
        )
    )
    await db.commit()

    assert await _run_saved_search_alerts() is True
    await _clear_throttle()
    assert await _run_saved_search_alerts() is True  # bypassed throttle

    notifications = (
        (
            await db.execute(
                select(Notification).where(Notification.kind == "saved_search")
            )
        )
        .scalars()
        .all()
    )
    # Same property is never alerted twice for the same search
    assert len(notifications) == 1

    # A fresh property published later IS alerted
    await _clear_throttle()
    await _make_active_property(client, str(user.id), db, "Yeni dedup elanı")
    assert await _run_saved_search_alerts() is True
    notifications = (
        (
            await db.execute(
                select(Notification).where(Notification.kind == "saved_search")
            )
        )
        .scalars()
        .all()
    )
    assert len(notifications) == 2


@pytest.mark.asyncio
async def test_email_disabled_skips_email_but_keeps_notification(
    client, auth_user, db, feature_catalog, monkeypatch
):
    from app.services.saved_search_alerts import _run_saved_search_alerts

    await _clear_throttle()
    user = await auth_user(email="digest3@test.az", is_verified=True)
    await _make_active_property(client, str(user.id), db, "Email off")

    db.add(
        SavedSearch(
            user_id=user.id,
            name="No email",
            filters={"deal_type": "sale", "property_type": "apartment"},
            is_active=True,
            email_enabled=False,
        )
    )
    await db.commit()

    sent: list = []
    monkeypatch.setattr(
        "app.services.saved_search_alerts.send_email",
        lambda to, subject, text_body, *, html_body=None: sent.append(to),
    )

    assert await _run_saved_search_alerts() is True
    assert sent == []

    notifications = (
        (
            await db.execute(
                select(Notification).where(Notification.kind == "saved_search")
            )
        )
        .scalars()
        .all()
    )
    assert len(notifications) == 1


@pytest.mark.asyncio
async def test_unsubscribe_disables_search(client, auth_user, db, feature_catalog):
    from app.api.v1.endpoints.saved_search import unsubscribe_token

    user = await auth_user(email="unsub@test.az", is_verified=True)
    search = SavedSearch(
        user_id=user.id, name="Abunə", filters={"deal_type": "sale"}, is_active=True
    )
    db.add(search)
    await db.commit()
    await db.refresh(search)

    token = unsubscribe_token(search.id, user.id)
    response = await client.get(
        "/api/v1/saved-searches/unsubscribe",
        params={"search_id": str(search.id), "token": token},
    )
    assert response.status_code == 200
    assert response.json()["ok"] is True

    await db.refresh(search)
    assert search.is_active is False

    # Bad token rejected
    response = await client.get(
        "/api/v1/saved-searches/unsubscribe",
        params={"search_id": str(search.id), "token": "forged"},
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_saved_search_email_toggle_roundtrip(client, auth_user, db):
    await auth_user(email="toggle@test.az", is_verified=True)
    created = await client.post(
        "/api/v1/saved-searches",
        json={
            "name": "Kirayə",
            "filters": {"deal_type": "rent"},
            "email_enabled": True,
        },
    )
    assert created.status_code == 201, created.text
    search_id = created.json()["id"]

    updated = await client.patch(
        f"/api/v1/saved-searches/{search_id}", json={"email_enabled": False}
    )
    assert updated.status_code == 200
    assert updated.json()["email_enabled"] is False

    listed = (await client.get("/api/v1/saved-searches")).json()
    assert listed[0]["email_enabled"] is False
