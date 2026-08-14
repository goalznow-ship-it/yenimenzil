from __future__ import annotations

import uuid
from datetime import UTC, timedelta
from datetime import datetime as dt

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies.auth import get_current_user
from app.db.session import get_db
from app.models.enums import PropertyStatus, UserRole
from app.models.payment import Payment
from app.models.promotion import PromotionProduct, PromotionPurchase
from app.models.property import Property
from app.models.user import User
from app.models.wallet import WalletTransaction
from app.schemas.payment import (
    PaymentListRead,
    PaymentRead,
    TopUpRead,
    TopUpRequest,
)
from app.schemas.wallet import (
    MyPromotionRead,
    PromotionCatalogItem,
    PromotionPurchaseRead,
    PromotionPurchaseRequest,
    WalletRead,
    WalletTransactionRead,
)
from app.services.payments import (
    PaymentError,
    cancel_payment,
    create_top_up_payment,
    get_or_create_wallet,
    get_payment,
)

router = APIRouter(prefix="/wallet", tags=["wallet"])


@router.get("", response_model=WalletRead)
async def get_wallet(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> WalletRead:
    wallet = await get_or_create_wallet(db, current_user.id)
    await db.commit()
    return wallet


@router.get("/transactions", response_model=list[WalletTransactionRead])
async def list_transactions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[WalletTransactionRead]:
    wallet = await get_or_create_wallet(db, current_user.id)
    result = await db.execute(
        select(WalletTransaction)
        .where(WalletTransaction.wallet_id == wallet.id)
        .order_by(WalletTransaction.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    transactions = result.scalars().all()
    await db.commit()
    return list(transactions)


@router.post("/top-up", response_model=TopUpRead, status_code=status.HTTP_202_ACCEPTED)
async def request_top_up(
    payload: TopUpRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TopUpRead:
    """Create a pending payment for a wallet top-up.

    Payment success is never trusted from the frontend: the wallet is
    credited only after a verified webhook or an explicit admin
    confirmation. The idempotency key prevents duplicate payments on retry.
    """
    await get_or_create_wallet(db, current_user.id)
    try:
        payment = await create_top_up_payment(
            db,
            user_id=current_user.id,
            amount=payload.amount,
            idempotency_key=payload.idempotency_key,
            note=payload.note,
        )
    except PaymentError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    await db.commit()
    await db.refresh(payment)
    return TopUpRead(payment=payment)


@router.get("/payments", response_model=list[PaymentListRead])
async def list_my_payments(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[PaymentListRead]:
    result = await db.execute(
        select(Payment)
        .where(Payment.user_id == current_user.id)
        .order_by(Payment.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    return list(result.scalars().all())


@router.post("/payments/{payment_id}/cancel", response_model=PaymentRead)
async def cancel_top_up_payment(
    payment_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PaymentRead:
    payment = await get_payment(db, payment_id)
    if payment is None or payment.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Payment not found")
    try:
        await cancel_payment(db, payment)
    except PaymentError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    await db.commit()
    await db.refresh(payment)
    return payment


@router.get("/promotions/catalog", response_model=list[PromotionCatalogItem])
async def promotion_catalog(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[PromotionCatalogItem]:
    """Catalog of enabled promotion products, configured by admins."""
    result = await db.execute(
        select(PromotionProduct)
        .where(PromotionProduct.enabled.is_(True))
        .order_by(PromotionProduct.sort_order, PromotionProduct.created_at)
    )
    products = result.scalars().all()
    return [
        PromotionCatalogItem(
            tier=p.code,
            label=p.label_az,
            price=p.price,
            days=p.duration_days,
            description=p.description_az,
            enabled=p.enabled,
        )
        for p in products
    ]


@router.get("/promotions", response_model=list[MyPromotionRead])
async def my_promotions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[MyPromotionRead]:
    """Active/expired promotion purchases for the current user's listings."""
    result = await db.execute(
        select(PromotionPurchase, PromotionProduct, Property.title)
        .join(PromotionProduct, PromotionProduct.id == PromotionPurchase.product_id)
        .join(Property, Property.id == PromotionPurchase.property_id)
        .where(Property.owner_id == current_user.id)
        .order_by(PromotionPurchase.created_at.desc())
        .limit(200)
    )
    return [
        MyPromotionRead(
            id=purchase.id,
            property_id=purchase.property_id,
            tier=product.code,
            label=product.label_az,
            price_paid=purchase.price_paid,
            status=purchase.status,
            starts_at=purchase.starts_at,
            ends_at=purchase.ends_at,
            property_title=title,
        )
        for purchase, product, title in result.all()
    ]


@router.post("/promotions", response_model=PromotionPurchaseRead)
async def purchase_promotion(
    payload: PromotionPurchaseRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PromotionPurchaseRead:
    product = await db.execute(
        select(PromotionProduct).where(PromotionProduct.code == payload.tier)
    )
    product = product.scalar_one_or_none()
    if product is None:
        raise HTTPException(status_code=400, detail="Unknown promotion product")
    if not product.enabled:
        raise HTTPException(status_code=400, detail="Promotion product is disabled")

    property = await db.get(Property, payload.property_id)
    if property is None:
        raise HTTPException(status_code=404, detail="Property not found")
    if property.owner_id != current_user.id and current_user.role not in (
        UserRole.ADMIN.value,
        UserRole.SUPER_ADMIN.value,
        UserRole.MODERATOR.value,
    ):
        raise HTTPException(
            status_code=403, detail="Only the owner can promote this listing"
        )
    if property.status != PropertyStatus.ACTIVE.value:
        raise HTTPException(
            status_code=400, detail="Only active listings can be promoted"
        )

    wallet = await get_or_create_wallet(db, current_user.id)

    active_dup = await db.execute(
        select(PromotionPurchase.id).where(
            PromotionPurchase.property_id == property.id,
            PromotionPurchase.product_id == product.id,
            PromotionPurchase.status == "active",
        )
    )
    if active_dup.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=409,
            detail="This listing already has an active purchase of the same "
            "promotion product",
        )

    if wallet.balance < product.price:
        raise HTTPException(
            status_code=402,
            detail="Insufficient wallet balance. Please top up your wallet first.",
        )

    wallet.balance -= product.price
    transaction = WalletTransaction(
        wallet_id=wallet.id,
        amount=-product.price,
        type="debit",
        status="completed",
        reason="promotion",
        reference_type="property",
        reference_id=property.id,
        note=f"{product.label_az} promosiyası",
    )
    db.add(transaction)
    await db.flush()

    # Apply promotion to the listing and record the purchase
    now = dt.now(UTC)
    base = (
        property.promotion_expires_at
        if property.promotion_expires_at and property.promotion_expires_at > now
        else now
    )
    ends_at = base + timedelta(days=product.duration_days)
    property.is_promoted = True
    property.is_premium = product.is_premium_tier
    property.promotion_tier = product.code
    property.promotion_expires_at = ends_at

    purchase = PromotionPurchase(
        property_id=property.id,
        product_id=product.id,
        price_paid=product.price,
        status="active",
        starts_at=now,
        ends_at=ends_at,
    )
    db.add(purchase)

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=409,
            detail="This listing already has an active purchase of the same "
            "promotion product",
        ) from None
    await db.refresh(transaction)
    return PromotionPurchaseRead(
        transaction=transaction,
        promotion_status="active",
        expires_at=ends_at,
        purchase_id=purchase.id,
    )
