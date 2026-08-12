from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies.auth import get_current_user
from app.db.session import get_db
from app.models.enums import UserRole
from app.models.property import Property
from app.models.user import User
from app.services.admin_log import log_admin_action

router = APIRouter(tags=["admin-promotions"])


def get_senior_admin_user(
    current_user: User = Depends(get_current_user),
) -> User:
    if current_user.role not in (UserRole.ADMIN, UserRole.SUPER_ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )
    return current_user


PROMOTION_TIERS = {
    "standard": {"label_az": "Standart", "days": 7},
    "premium": {"label_az": "Premium", "days": 14},
    "vip": {"label_az": "VIP", "days": 30},
    "top": {"label_az": "Top", "days": 30},
    "urgent": {"label_az": "Təcili (Urgent)", "days": 3},
}


class PromotionRequest(BaseModel):
    tier: str = Field(pattern="^(standard|premium|vip|top|urgent)$")
    days: int | None = Field(None, ge=1, le=365)


def _promotion_status(prop: Property, now: datetime) -> str:
    if prop.is_promoted or prop.is_premium:
        if prop.expires_at and prop.expires_at < now:
            return "expired"
        return "active"
    return "none"


@router.get("/admin/promotions/listings")
async def admin_list_promoted_listings(
    admin_user: User = Depends(get_senior_admin_user),
    db: AsyncSession = Depends(get_db),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    status_filter: str | None = Query(default=None, alias="status", pattern="^(active|expired|none)$"),
    search: str | None = Query(default=None),
) -> dict[str, Any]:
    """List listings with their promotion status and tier."""
    query = select(Property)
    if search:
        query = query.where(Property.title.ilike(f"%{search}%"))
    if status_filter == "active":
        query = query.where(Property.expires_at >= datetime.now(UTC))
    elif status_filter == "expired":
        query = query.where(Property.expires_at < datetime.now(UTC))
    elif status_filter == "none":
        pass

    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar() or 0
    query = query.order_by(Property.created_at.desc()).offset((page - 1) * limit).limit(limit)
    props = (await db.execute(query)).scalars().all()
    now = datetime.now(UTC)

    data = []
    for prop in props:
        tier = None
        if prop.is_premium:
            tier = "premium"
        elif prop.is_promoted:
            tier = "vip"
        data.append({
            "id": str(prop.id),
            "title": prop.title,
            "reference_code": prop.reference_code,
            "status": prop.status.value if hasattr(prop.status, "value") else prop.status,
            "tier": tier,
            "is_premium": prop.is_premium,
            "is_promoted": prop.is_promoted,
            "promotion_status": _promotion_status(prop, now),
            "expires_at": prop.expires_at.isoformat() if prop.expires_at else None,
        })

    return {
        "data": data,
        "pagination": {"page": page, "limit": limit, "total": total, "pages": (total + limit - 1) // limit},
        "tiers": PROMOTION_TIERS,
    }


@router.post("/admin/promotions/listings/{property_id}/activate")
async def admin_activate_promotion(
    property_id: uuid.UUID,
    promo: PromotionRequest,
    admin_user: User = Depends(get_senior_admin_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Activate a promotion tier for a listing."""
    prop = await db.get(Property, property_id)
    if not prop:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Listing not found",
        )

    days = promo.days or PROMOTION_TIERS[promo.tier]["days"]
    expiry = datetime.now(UTC) + timedelta(days=days)

    if promo.tier == "premium":
        prop.is_premium = True
        prop.is_promoted = True
    elif promo.tier == "top" or promo.tier == "vip" or promo.tier == "urgent":
        prop.is_promoted = True
    else:  # standard — no paid badge, just order boost signal
        prop.is_promoted = False
    prop.expires_at = expiry

    await db.flush()
    await log_admin_action(
        db,
        admin_id=admin_user.id,
        action="promotion.activate",
        entity_type="property",
        entity_id=property_id,
        details={"tier": promo.tier, "days": days, "expires_at": expiry.isoformat()},
    )
    await db.commit()

    return {
        "message": "Promotion activated",
        "tier": promo.tier,
        "expires_at": expiry.isoformat(),
    }


@router.post("/admin/promotions/listings/{property_id}/deactivate")
async def admin_deactivate_promotion(
    property_id: uuid.UUID,
    admin_user: User = Depends(get_senior_admin_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Remove promotion flags from a listing."""
    prop = await db.get(Property, property_id)
    if not prop:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Listing not found",
        )

    prop.is_premium = False
    prop.is_promoted = False
    prop.expires_at = None

    await db.flush()
    await log_admin_action(
        db,
        admin_id=admin_user.id,
        action="promotion.deactivate",
        entity_type="property",
        entity_id=property_id,
    )
    await db.commit()

    return {"message": "Promotion removed", "property_id": str(property_id)}


admin_promotions_router = APIRouter()
admin_promotions_router.include_router(router, prefix="")