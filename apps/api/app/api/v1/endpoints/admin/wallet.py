from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies.auth import get_current_user
from app.db.session import get_db
from app.models.payment import Payment, PaymentStatus
from app.models.user import User
from app.schemas.payment import PaymentListRead, PaymentRead
from app.services.admin_log import log_admin_action
from app.services.payments import (
    PaymentError,
    cancel_payment,
    confirm_payment,
    fail_payment,
    get_payment,
    refund_payment,
)

router = APIRouter(tags=["admin-wallet"])

admin_wallet_router = router


def get_senior_admin_user(
    current_user: User = Depends(get_current_user),
) -> User:
    if current_user.role not in ("admin", "super_admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )
    return current_user


@router.get("/admin/payments", response_model=list[PaymentListRead])
async def admin_list_payments(
    current_user: User = Depends(get_senior_admin_user),
    db: AsyncSession = Depends(get_db),
    status_filter: str | None = Query(default=None, alias="status"),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> list[PaymentListRead]:
    stmt = select(Payment).order_by(Payment.created_at.desc())
    if status_filter:
        stmt = stmt.where(Payment.status == status_filter)
    stmt = stmt.offset(offset).limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all())


@router.get("/admin/payments/{payment_id}", response_model=PaymentRead)
async def admin_get_payment(
    payment_id: uuid.UUID,
    current_user: User = Depends(get_senior_admin_user),
    db: AsyncSession = Depends(get_db),
) -> PaymentRead:
    payment = await get_payment(db, payment_id)
    if payment is None:
        raise HTTPException(status_code=404, detail="Payment not found")
    return payment


@router.post(
    "/admin/payments/{payment_id}/confirm",
    response_model=PaymentRead,
)
async def admin_confirm_payment(
    payment_id: uuid.UUID,
    current_user: User = Depends(get_senior_admin_user),
    db: AsyncSession = Depends(get_db),
) -> PaymentRead:
    """Confirm a pending payment and credit the wallet (manual/mock providers)."""
    payment = await get_payment(db, payment_id)
    if payment is None:
        raise HTTPException(status_code=404, detail="Payment not found")
    try:
        await confirm_payment(db, payment)
    except PaymentError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    await db.commit()
    await db.refresh(payment)
    await log_admin_action(
        db,
        admin_id=current_user.id,
        action="payment.confirm",
        entity_type="payment",
        entity_id=payment.id,
        details={"amount": payment.amount},
    )
    return payment


@router.post(
    "/admin/payments/{payment_id}/reject",
    response_model=PaymentRead,
)
async def admin_reject_payment(
    payment_id: uuid.UUID,
    current_user: User = Depends(get_senior_admin_user),
    db: AsyncSession = Depends(get_db),
) -> PaymentRead:
    """Reject (fail) a pending payment without crediting the wallet."""
    payment = await get_payment(db, payment_id)
    if payment is None:
        raise HTTPException(status_code=404, detail="Payment not found")
    try:
        await fail_payment(db, payment, "Rejected by administrator")
    except PaymentError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    await db.commit()
    await db.refresh(payment)
    await log_admin_action(
        db,
        admin_id=current_user.id,
        action="payment.reject",
        entity_type="payment",
        entity_id=payment.id,
        details={"amount": payment.amount},
    )
    return payment


@router.post(
    "/admin/payments/{payment_id}/cancel",
    response_model=PaymentRead,
)
async def admin_cancel_payment(
    payment_id: uuid.UUID,
    current_user: User = Depends(get_senior_admin_user),
    db: AsyncSession = Depends(get_db),
) -> PaymentRead:
    payment = await get_payment(db, payment_id)
    if payment is None:
        raise HTTPException(status_code=404, detail="Payment not found")
    try:
        await cancel_payment(db, payment)
    except PaymentError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    await db.commit()
    await db.refresh(payment)
    await log_admin_action(
        db,
        admin_id=current_user.id,
        action="payment.cancel",
        entity_type="payment",
        entity_id=payment.id,
    )
    return payment


@router.post(
    "/admin/payments/{payment_id}/refund",
    response_model=PaymentRead,
)
async def admin_refund_payment(
    payment_id: uuid.UUID,
    current_user: User = Depends(get_senior_admin_user),
    db: AsyncSession = Depends(get_db),
) -> PaymentRead:
    """Refund a paid payment: provider refund + wallet debit."""
    payment = await get_payment(db, payment_id)
    if payment is None:
        raise HTTPException(status_code=404, detail="Payment not found")
    try:
        await refund_payment(db, payment)
    except PaymentError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    await db.commit()
    await db.refresh(payment)
    await log_admin_action(
        db,
        admin_id=current_user.id,
        action="payment.refund",
        entity_type="payment",
        entity_id=payment.id,
        details={"amount": payment.amount},
    )
    return payment


@router.get("/admin/wallet/top-ups", response_model=list[PaymentListRead])
async def admin_list_top_ups(
    current_user: User = Depends(get_senior_admin_user),
    db: AsyncSession = Depends(get_db),
    status_filter: str | None = Query(default=None, alias="status"),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> list[PaymentListRead]:
    stmt = (
        select(Payment)
        .where(Payment.status == (status_filter or PaymentStatus.PENDING))
        .order_by(Payment.created_at.desc())
    )
    stmt = stmt.offset(offset).limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all())
