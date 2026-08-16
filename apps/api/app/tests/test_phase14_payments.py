"""Phase 14: payment go-live boundary (webhook observability, admin payments)."""

from __future__ import annotations

import pytest


def _mock_webhook_signature(payload: bytes, secret: str = "mock-dev-secret") -> str:
    import hashlib
    import hmac

    return hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()


def _send_webhook(client, provider_payment_id: str):
    import json

    body = json.dumps(
        {"event_type": "payment.succeeded", "object": {"id": provider_payment_id}}
    ).encode()
    return client.post(
        "/api/v1/webhooks/payments/mock",
        content=body,
        headers={
            "x-provider-signature": _mock_webhook_signature(body),
            "content-type": "application/json",
        },
    )


async def _create_pending_payment(client, user_id, db):
    from app.models.payment import Payment

    payment = Payment(
        user_id=user_id,
        idempotency_key="phase14-pending-1",
        amount=50_000,
        currency="AZN",
        provider="mock",
        provider_payment_id="mock_phase14_1",
    )
    db.add(payment)
    await db.commit()
    return payment


@pytest.mark.asyncio
async def test_webhook_failure_recorded(client, auth_user, db):
    await auth_user(email="wh-fail@test.az")
    response = await client.post(
        "/api/v1/webhooks/payments/mock",
        content=b'{"bad": "payload"}',
        headers={"x-provider-signature": "nope", "content-type": "application/json"},
    )
    assert response.status_code == 401

    from app.models.webhook_event import WebhookEvent

    events = (
        (
            await db.execute(
                __import__("sqlalchemy")
                .select(WebhookEvent)
                .order_by(WebhookEvent.created_at.desc())
            )
        )
        .scalars()
        .all()
    )
    assert events, "no webhook event recorded"
    assert events[0].status == "failed"
    assert events[0].provider == "mock"


@pytest.mark.asyncio
async def test_webhook_processed_recorded(client, auth_user, db):
    user = await auth_user(email="wh-ok@test.az", is_verified=True)
    payment = await _create_pending_payment(client, user.id, db)

    response = await _send_webhook(client, payment.provider_payment_id)
    assert response.status_code == 200
    assert response.json()["status"] == "processed"

    from app.models.webhook_event import WebhookEvent

    events = (
        (
            await db.execute(
                __import__("sqlalchemy")
                .select(WebhookEvent)
                .where(WebhookEvent.status == "processed")
            )
        )
        .scalars()
        .all()
    )
    assert events
    assert events[-1].payment_id == payment.id
    assert events[-1].event_type == "payment.succeeded"

    # wallet credited (50_000 units = 500 AZN)
    wallet = (await client.get("/api/v1/wallet")).json()
    assert wallet["balance"] == 50_000


@pytest.mark.asyncio
async def test_admin_payments_summary_and_webhooks(client, auth_user, db):
    admin = await auth_user(email="admin-payments@test.az", is_verified=True)
    admin.role = "admin"
    await db.commit()

    payment = await _create_pending_payment(client, admin.id, db)
    response = await _send_webhook(client, payment.provider_payment_id)
    assert response.status_code == 200

    summary = await client.get("/api/v1/admin/payments/summary")
    assert summary.status_code == 200, summary.text
    data = summary.json()
    assert data["revenue_azn"] == 500.0
    assert data["by_status"]["paid"]["count"] == 1
    assert "webhook_counts" in data

    events = await client.get("/api/v1/admin/payments/webhook-events")
    assert events.status_code == 200
    rows = events.json()
    assert rows, "webhook events list empty"
    assert rows[0]["provider"] == "mock"
    assert rows[0]["status"] in ("processed", "failed")

    # provider filter on payments list
    listed = await client.get("/api/v1/admin/payments?provider=mock")
    assert listed.status_code == 200
    assert any(p["id"] == str(payment.id) for p in listed.json())
