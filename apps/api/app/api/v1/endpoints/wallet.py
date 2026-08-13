from __future__ import annotations

from datetime import UTC, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies.auth import get_current_user
from app.db.session import get_db
from app.models.enums import PropertyStatus, UserRole
from app.models.property import Property
from app.models.user import User
from app.models.wallet import Wallet, WalletTransaction
from app.schemas.wallet import (
    PROMOTION_TIERS,
    PromotionCatalogItem,
    PromotionPurchaseRead,
    PromotionPurchaseRequest,
    TopUpRead,
    TopUpRequest,
    WalletRead,
    WalletTransactionRead,
)

router = APIRouter(prefix="/wallet", tags=["wallet"])


async def _get_or_create_wallet(db: AsyncSession, user: User) -> Wallet:
    wallet = await db.execute(select(Wallet).where(Wallet.user_id == user.id))
    wallet = wallet.scalar_one_or_none()
    if wallet is None:
        wallet = Wallet(user_id=user.id, balance=0)
        db.add(wallet)
        await db.flush()
    return wallet


@router.get("", response_model=WalletRead)
async def get_wallet(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> WalletRead:
    wallet = await _get_or_create_wallet(db, current_user)
    await db.commit()
    return wallet


@router.get("/transactions", response_model=list[WalletTransactionRead])
async def list_transactions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[WalletTransactionRead]:
    wallet = await _get_or_create_wallet(db, current_user)
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
    """Request a credit top-up. A real payment gateway is not configured yet,
    so the transaction is created as PENDING and must be confirmed by an
    admin. Payment success is never faked."""
    wallet = await _get_or_create_wallet(db, current_user)
    transaction = WalletTransaction(
        wallet_id=wallet.id,
        amount=payload.amount,
        type="credit",
        status="pending",
        reason="top_up",
        note=payload.note,
    )
    db.add(transaction)
    await db.commit()
    await db.refresh(transaction)
    return TopUpRead(transaction=transaction)


@router.get("/promotions/catalog", response_model=list[PromotionCatalogItem])
async def promotion_catalog(
    current_user: User = Depends(get_current_user),
) -> list[PromotionCatalogItem]:
    descriptions = {
        "standard": "7 gün standart önə çıxarış",
        "premium": "14 gün premium yerləşdirmə",
        "vip": "30 gün VIP nişanı",
        "top": "30 gün siyahının ən yuxarısı",
        "urgent": "7 gün təcili nişanı",
    }
    return [
        PromotionCatalogItem(
            tier=tier,
            label=cfg["label"],
            price=cfg["price"],
            days=cfg["days"],
            description=descriptions.get(tier, ""),
        )
        for tier, cfg in PROMOTION_TIERS.items()
    ]


@router.post("/promotions", response_model=PromotionPurchaseRead)
async def purchase_promotion(
    payload: PromotionPurchaseRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PromotionPurchaseRead:
    tier_cfg = PROMOTION_TIERS.get(payload.tier)
    if tier_cfg is None:
        raise HTTPException(status_code=400, detail="Unknown promotion tier")

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

    wallet = await _get_or_create_wallet(db, current_user)
    if wallet.balance < tier_cfg["price"]:
        raise HTTPException(
            status_code=402,
            detail="Insufficient wallet balance. Please top up your wallet first.",
        )

    wallet.balance -= tier_cfg["price"]
    transaction = WalletTransaction(
        wallet_id=wallet.id,
        amount=-tier_cfg["price"],
        type="debit",
        status="completed",
        reason="promotion",
        reference_type="property",
        reference_id=property.id,
        note=f"{tier_cfg['label']} promosiyası",
    )
    db.add(transaction)

    # Apply promotion to the listing
    from datetime import datetime as dt

    property.is_promoted = True
    property.is_premium = payload.tier in ("premium", "vip", "top")
    property.promotion_tier = payload.tier
    now = dt.now(UTC)
    base = (
        property.promotion_expires_at
        if property.promotion_expires_at and property.promotion_expires_at > now
        else now
    )
    property.promotion_expires_at = base + timedelta(days=tier_cfg["days"])

    await db.commit()
    await db.refresh(transaction)
    return PromotionPurchaseRead(
        transaction=transaction,
        promotion_status="active",
        expires_at=property.promotion_expires_at,
    )
