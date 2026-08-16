"""Provider webhook endpoint.

Never trusts the frontend: payments are only credited after a verified
webhook (or an explicit admin confirmation). Signature verification is
performed by the configured provider before any state change.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request, status
from sqlalchemy import select

from app.db.session import async_session_factory
from app.models.payment import Payment
from app.models.webhook_event import WebhookEvent
from app.services.payments.provider import ProviderError, get_payment_provider

router = APIRouter(prefix="/webhooks", tags=["webhooks"])

SIGNATURE_HEADERS = {
    "stripe": "stripe-signature",
    "mock": "x-provider-signature",
}


async def _record_webhook(
    provider: str,
    status_: str,
    event_type: str | None = None,
    payment_id=None,
    error: str | None = None,
    payload: dict | None = None,
) -> None:
    """Persist a webhook delivery outcome for admin observability."""
    try:
        async with async_session_factory() as db:
            db.add(
                WebhookEvent(
                    provider=provider,
                    status=status_,
                    event_type=event_type,
                    payment_id=payment_id,
                    error=error[:500] if error else None,
                    payload_snapshot=payload or {},
                )
            )
            await db.commit()
    except Exception:  # noqa: BLE001, S110 - observability must never break the webhook path
        pass


@router.post("/payments/{provider}", status_code=status.HTTP_200_OK)
async def payment_webhook(provider: str, request: Request) -> dict[str, str]:
    """Receive and process provider webhooks idempotently."""
    payload = await request.body()
    signature = request.headers.get(SIGNATURE_HEADERS.get(provider, ""))
    if not payload:
        await _record_webhook(provider, "failed", error="empty body")
        raise HTTPException(status_code=400, detail="Empty webhook body")

    active = get_payment_provider()
    if active.name != provider:
        await _record_webhook(provider, "failed", error="inactive provider")
        raise HTTPException(
            status_code=400,
            detail=f"Webhook for '{provider}' is not accepted; "
            f"active provider is '{active.name}'",
        )

    try:
        event = active.verify_webhook(payload, signature)
    except ProviderError as exc:
        await _record_webhook(provider, "failed", error=str(exc))
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    except ValueError as exc:
        await _record_webhook(provider, "failed", error="malformed payload")
        raise HTTPException(
            status_code=400, detail="Malformed webhook payload"
        ) from exc

    event_type = event.get("event_type", "")
    obj = event.get("object") or {}
    provider_payment_id = obj.get("id") if isinstance(obj, dict) else None
    if not provider_payment_id:
        await _record_webhook(provider, "ignored", event_type, payload=event)
        return {"status": "ignored", "reason": "no payment id"}

    async with async_session_factory() as db:
        result = await db.execute(
            select(Payment).where(
                Payment.provider == provider,
                Payment.provider_payment_id == provider_payment_id,
            )
        )
        payment = result.scalar_one_or_none()
        if payment is None:
            await _record_webhook(provider, "ignored", event_type, payload=event)
            return {"status": "ignored", "reason": "unknown payment"}

        if event_type in ("payment.succeeded", "charge.succeeded"):
            if payment.status == "pending":
                from app.services.payments.service import confirm_payment

                await confirm_payment(db, payment)
            await db.commit()
            await _record_webhook(
                provider,
                "processed",
                event_type,
                payment_id=payment.id,
                payload=event,
            )
            return {"status": "processed", "event": event_type}

        if event_type in ("payment.failed", "charge.failed"):
            if payment.status == "pending":
                from app.services.payments.service import fail_payment

                await fail_payment(
                    db,
                    payment,
                    (obj.get("failure_message") if isinstance(obj, dict) else None)
                    or "gateway declined",
                )
            await db.commit()
            await _record_webhook(
                provider,
                "processed",
                event_type,
                payment_id=payment.id,
                payload=event,
            )
            return {"status": "processed", "event": event_type}

        await _record_webhook(
            provider, "ignored", event_type, payment_id=payment.id, payload=event
        )
        return {"status": "ignored", "event": event_type}
