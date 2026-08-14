"""Payment service: create/confirm/fail/cancel/refund with idempotency.

All wallet credits/debits happen here, guarded by idempotency keys so a
duplicate webhook or retried request can never double-credit a wallet.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.payment import Payment, PaymentStatus
from app.models.wallet import Wallet, WalletTransaction
from app.services.payments.provider import (
    ProviderError,
    get_payment_provider,
)

MIN_TOP_UP = 100
MAX_TOP_UP = 1_000_000


class PaymentError(Exception):
    """Domain error raised by the payment service."""


async def get_or_create_wallet(db: AsyncSession, user_id: uuid.UUID) -> Wallet:
    wallet = await db.execute(select(Wallet).where(Wallet.user_id == user_id))
    wallet = wallet.scalar_one_or_none()
    if wallet is None:
        wallet = Wallet(user_id=user_id, balance=0)
        db.add(wallet)
        await db.flush()
    return wallet


async def create_top_up_payment(
    db: AsyncSession,
    user_id: uuid.UUID,
    amount: int,
    idempotency_key: str,
    note: str | None = None,
) -> Payment:
    """Create a pending payment. Idempotent on (user_id, idempotency_key).

    Raises PaymentError if the key was already used with a different amount.
    """
    if not MIN_TOP_UP <= amount <= MAX_TOP_UP:
        raise PaymentError(f"Amount must be between {MIN_TOP_UP} and {MAX_TOP_UP}")
    if not idempotency_key or len(idempotency_key) > 200:
        raise PaymentError("A valid idempotency key is required")

    existing = await db.execute(
        select(Payment).where(
            Payment.user_id == user_id,
            Payment.idempotency_key == idempotency_key,
        )
    )
    existing = existing.scalar_one_or_none()
    if existing is not None:
        if existing.amount != amount:
            raise PaymentError("Idempotency key reused with a different amount")
        return existing

    provider = get_payment_provider()
    try:
        result = await provider.create_payment(
            amount=amount,
            currency="AZN",
            idempotency_key=idempotency_key,
            description=f"Wallet top-up {amount} AZN",
        )
    except ProviderError as exc:
        raise PaymentError(f"Payment provider error: {exc}") from exc

    payment = Payment(
        user_id=user_id,
        idempotency_key=idempotency_key,
        amount=amount,
        currency="AZN",
        status=PaymentStatus.PENDING,
        provider=provider.name,
        provider_payment_id=result.provider_payment_id,
        checkout_url=result.checkout_url,
        note=note,
    )
    db.add(payment)
    try:
        await db.flush()
    except IntegrityError as exc:
        raise PaymentError("Idempotency conflict") from exc
    return payment


async def confirm_payment(db: AsyncSession, payment: Payment) -> Payment:
    """Mark a pending payment as paid and credit the wallet.

    Safe to call multiple times (idempotent).
    """
    if payment.status == PaymentStatus.PAID:
        return payment
    if payment.status not in (PaymentStatus.PENDING,):
        raise PaymentError(f"Cannot confirm payment in state {payment.status}")

    wallet = await get_or_create_wallet(db, payment.user_id)
    wallet.balance += payment.amount

    transaction = WalletTransaction(
        wallet_id=wallet.id,
        amount=payment.amount,
        type="credit",
        status="completed",
        reason="top_up",
        reference_type="payment",
        reference_id=payment.id,
        note=payment.note,
    )
    db.add(transaction)
    await db.flush()

    payment.status = PaymentStatus.PAID
    payment.wallet_transaction_id = transaction.id
    return payment


async def fail_payment(
    db: AsyncSession, payment: Payment, reason: str | None
) -> Payment:
    if payment.status != PaymentStatus.PENDING:
        raise PaymentError(f"Cannot fail payment in state {payment.status}")
    payment.status = PaymentStatus.FAILED
    payment.failure_reason = reason
    return payment


async def cancel_payment(db: AsyncSession, payment: Payment) -> Payment:
    if payment.status != PaymentStatus.PENDING:
        raise PaymentError(f"Cannot cancel payment in state {payment.status}")
    payment.status = PaymentStatus.CANCELLED
    return payment


async def refund_payment(db: AsyncSession, payment: Payment) -> Payment:
    """Refund a paid payment: reverse the wallet credit.

    Only paid payments can be refunded. Idempotent.
    """
    if payment.status == PaymentStatus.REFUNDED:
        return payment
    if payment.status != PaymentStatus.PAID:
        raise PaymentError(f"Cannot refund payment in state {payment.status}")

    provider = get_payment_provider()
    if payment.provider_payment_id:
        try:
            await provider.refund_payment(payment.provider_payment_id)
        except ProviderError as exc:
            raise PaymentError(f"Provider refund failed: {exc}") from exc

    if payment.wallet_transaction_id is not None:
        wallet = await get_or_create_wallet(db, payment.user_id)
        wallet.balance = max(0, wallet.balance - payment.amount)
        db.add(
            WalletTransaction(
                wallet_id=wallet.id,
                amount=-payment.amount,
                type="debit",
                status="completed",
                reason="refund",
                reference_type="payment",
                reference_id=payment.id,
                note="Top-up geri qaytarılması",
            )
        )

    payment.status = PaymentStatus.REFUNDED
    payment.refunded_at = datetime.now(UTC)
    return payment


async def get_payment_by_idempotency(
    db: AsyncSession, user_id: uuid.UUID, key: str
) -> Payment | None:
    result = await db.execute(
        select(Payment).where(
            Payment.user_id == user_id,
            Payment.idempotency_key == key,
        )
    )
    return result.scalar_one_or_none()


async def get_payment(db: AsyncSession, payment_id: uuid.UUID) -> Payment | None:
    return await db.get(Payment, payment_id)
