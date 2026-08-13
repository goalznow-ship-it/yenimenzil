from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies.auth import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.models.wallet import Wallet, WalletTransaction
from app.schemas.wallet import AdminConfirmTopUpRequest, WalletTransactionRead

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


@router.get("/admin/wallet/top-ups", response_model=list[WalletTransactionRead])
async def admin_list_top_ups(
    current_user: User = Depends(get_senior_admin_user),
    db: AsyncSession = Depends(get_db),
    status_filter: str | None = Query(default="pending", alias="status"),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> list[WalletTransactionRead]:
    stmt = (
        select(WalletTransaction)
        .join(Wallet, Wallet.id == WalletTransaction.wallet_id)
        .where(
            WalletTransaction.type == "credit",
            WalletTransaction.reason == "top_up",
        )
    )
    if status_filter:
        stmt = stmt.where(WalletTransaction.status == status_filter)
    stmt = (
        stmt.order_by(WalletTransaction.created_at.desc()).offset(offset).limit(limit)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


@router.post(
    "/admin/wallet/top-ups/{transaction_id}/confirm",
    response_model=WalletTransactionRead,
)
async def admin_confirm_top_up(
    transaction_id: uuid.UUID,
    payload: AdminConfirmTopUpRequest,
    current_user: User = Depends(get_senior_admin_user),
    db: AsyncSession = Depends(get_db),
) -> WalletTransactionRead:
    transaction = await db.get(WalletTransaction, transaction_id)
    if transaction is None:
        raise HTTPException(status_code=404, detail="Top-up not found")
    if transaction.type != "credit" or transaction.reason != "top_up":
        raise HTTPException(status_code=400, detail="Not a top-up transaction")
    if transaction.status != "pending":
        raise HTTPException(
            status_code=400,
            detail="Only pending top-ups can be confirmed",
        )

    if payload.approve:
        wallet = await db.get(Wallet, transaction.wallet_id)
        if wallet is None:
            raise HTTPException(status_code=404, detail="Wallet not found")
        wallet.balance += transaction.amount
        transaction.status = "completed"
    else:
        transaction.status = "rejected"
        transaction.note = payload.note or transaction.note

    await db.commit()
    await db.refresh(transaction)
    return transaction
