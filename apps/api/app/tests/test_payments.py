"""Phase 10: payment architecture tests.

Covers idempotent top-up creation, webhook verification, wallet crediting,
cancellation and refunds. Payment success must never come from the frontend.
"""

from __future__ import annotations

import hashlib
import hmac
import json

import pytest


def _mock_webhook_signature(payload: bytes, secret: str = "mock-dev-secret") -> str:
    return hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()


def _mock_webhook(client, provider_payment_id: str, secret: str = "mock-dev-secret"):
    """Simulate the mock provider's webhook for a payment."""
    body = json.dumps(
        {"event_type": "payment.succeeded", "object": {"id": provider_payment_id}}
    ).encode()
    return client.post(
        "/api/v1/webhooks/payments/mock",
        content=body,
        headers={"x-provider-signature": _mock_webhook_signature(body, secret)},
    )


def _create_top_up(client, amount: int = 5000, key: str = "key-abc-12345678"):
    return client.post(
        "/api/v1/wallet/top-up",
        json={"amount": amount, "idempotency_key": key},
    )


@pytest.fixture()
async def seller(client, auth_user):
    user = await auth_user(email="pay@test.az", is_verified=True)
    return {"user": user}


async def test_top_up_creates_pending_payment(seller, client):
    resp = await _create_top_up(client)
    assert resp.status_code == 202, resp.text
    data = resp.json()["payment"]
    assert data["status"] == "pending"
    assert data["amount"] == 5000
    assert data["provider"] == "mock"
    assert data["provider_payment_id"].startswith("mock_")


async def test_top_up_is_idempotent(seller, client):
    first = await _create_top_up(client)
    second = await _create_top_up(client)
    assert first.status_code == 202
    assert second.status_code == 202
    assert first.json()["payment"]["id"] == second.json()["payment"]["id"]


async def test_top_up_same_key_different_amount_rejected(seller, client):
    ok = await _create_top_up(client, amount=5000)
    assert ok.status_code == 202
    bad = await _create_top_up(client, amount=6000)
    assert bad.status_code == 400
    assert "Idempotency key" in bad.json()["detail"]


async def test_top_up_validates_amount(seller, client):
    resp = await client.post(
        "/api/v1/wallet/top-up",
        json={"amount": 1, "idempotency_key": "key-abc-12345678"},
    )
    assert resp.status_code == 422


async def test_webhook_bad_signature_rejected(seller, client):
    resp = await _create_top_up(client)
    provider_id = resp.json()["payment"]["provider_payment_id"]
    body = json.dumps(
        {"event_type": "payment.succeeded", "object": {"id": provider_id}}
    ).encode()
    bad = await client.post(
        "/api/v1/webhooks/payments/mock",
        content=body,
        headers={"x-provider-signature": "deadbeef"},
    )
    assert bad.status_code == 401


async def test_webhook_confirm_credits_wallet(seller, client):
    resp = await _create_top_up(client)
    provider_id = resp.json()["payment"]["provider_payment_id"]

    wallet_before = (await client.get("/api/v1/wallet")).json()
    assert wallet_before["balance"] == 0

    hook = await _mock_webhook(client, provider_id)
    assert hook.status_code == 200, hook.text

    wallet_after = (await client.get("/api/v1/wallet")).json()
    assert wallet_after["balance"] == 5000


async def test_webhook_is_idempotent_no_double_credit(seller, client):
    resp = await _create_top_up(client)
    provider_id = resp.json()["payment"]["provider_payment_id"]

    await _mock_webhook(client, provider_id)
    await _mock_webhook(client, provider_id)

    wallet = (await client.get("/api/v1/wallet")).json()
    assert wallet["balance"] == 5000


async def test_webhook_unknown_provider_rejected(seller, client):
    body = json.dumps({"event_type": "x", "object": {"id": "nope"}}).encode()
    resp = await client.post(
        "/api/v1/webhooks/payments/nonexistent",
        content=body,
        headers={"x-provider-signature": "abc"},
    )
    assert resp.status_code == 400


async def test_cancel_payment_does_not_credit(seller, client):
    resp = await _create_top_up(client)
    payment_id = resp.json()["payment"]["id"]

    cancel = await client.post(f"/api/v1/wallet/payments/{payment_id}/cancel")
    assert cancel.status_code == 200
    assert cancel.json()["status"] == "cancelled"

    wallet = (await client.get("/api/v1/wallet")).json()
    assert wallet["balance"] == 0


async def test_user_cannot_manage_others_payment(seller, client, auth_user):
    resp = await _create_top_up(client)
    payment_id = resp.json()["payment"]["id"]

    await auth_user(email="pay2@test.az")

    cancel = await client.post(f"/api/v1/wallet/payments/{payment_id}/cancel")
    assert cancel.status_code == 404


async def test_admin_confirm_and_refund(seller, client, auth_user):
    resp = await _create_top_up(client)
    payment_id = resp.json()["payment"]["id"]

    # switch to admin, confirm, refund
    await auth_user(email="admin@test.az", role="admin")
    confirm = await client.post(f"/api/v1/admin/payments/{payment_id}/confirm")
    assert confirm.status_code == 200
    assert confirm.json()["status"] == "paid"

    refund = await client.post(f"/api/v1/admin/payments/{payment_id}/refund")
    assert refund.status_code == 200
    assert refund.json()["status"] == "refunded"

    # wallet must be debited back
    await auth_user(email="pay@test.az")
    wallet = (await client.get("/api/v1/wallet")).json()
    assert wallet["balance"] == 0


async def test_admin_refund_requires_admin(seller, client, auth_user):
    resp = await _create_top_up(client)
    payment_id = resp.json()["payment"]["id"]

    await auth_user(email="regular@test.az")
    denied = await client.post(f"/api/v1/admin/payments/{payment_id}/confirm")
    assert denied.status_code == 403


async def test_admin_list_payments(seller, client, auth_user):
    await _create_top_up(client)
    await auth_user(email="admin2@test.az", role="admin")
    listing = await client.get("/api/v1/admin/payments")
    assert listing.status_code == 200
    assert len(listing.json()) == 1
