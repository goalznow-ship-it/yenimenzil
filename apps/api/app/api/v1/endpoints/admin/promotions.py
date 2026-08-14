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
from app.models.promotion import PromotionProduct, PromotionPurchase
from app.models.property import Property
from app.models.user import User
from app.schemas.wallet import (
    PromotionProductAdminCreate,
    PromotionProductAdminRead,
    PromotionProductAdminUpdate,
)
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


class PromotionRequest(BaseModel):
    tier: str = Field(min_length=2, max_length=32)
    days: int | None = Field(None, ge=1, le=365)


# ---------- Promotion products (configurable paid listing products) ----------


@router.get(
    "/admin/promotions/products", response_model=list[PromotionProductAdminRead]
)
async def admin_list_promotion_products(
    admin_user: User = Depends(get_senior_admin_user),
    db: AsyncSession = Depends(get_db),
) -> list[PromotionProductAdminRead]:
    result = await db.execute(
        select(PromotionProduct).order_by(
            PromotionProduct.sort_order, PromotionProduct.created_at
        )
    )
    return list(result.scalars().all())


@router.post(
    "/admin/promotions/products",
    response_model=PromotionProductAdminRead,
    status_code=status.HTTP_201_CREATED,
)
async def admin_create_promotion_product(
    payload: PromotionProductAdminCreate,
    admin_user: User = Depends(get_senior_admin_user),
    db: AsyncSession = Depends(get_db),
) -> PromotionProductAdminRead:
    existing = await db.execute(
        select(PromotionProduct).where(PromotionProduct.code == payload.code)
    )
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(status_code=400, detail="Product code already exists")
    product = PromotionProduct(**payload.model_dump())
    db.add(product)
    await db.flush()
    await log_admin_action(
        db,
        admin_id=admin_user.id,
        action="promotion.product.create",
        entity_type="promotion_product",
        entity_id=product.id,
        details={"code": product.code, "price": product.price},
    )
    await db.commit()
    await db.refresh(product)
    return product


@router.patch(
    "/admin/promotions/products/{product_id}",
    response_model=PromotionProductAdminRead,
)
async def admin_update_promotion_product(
    product_id: uuid.UUID,
    payload: PromotionProductAdminUpdate,
    admin_user: User = Depends(get_senior_admin_user),
    db: AsyncSession = Depends(get_db),
) -> PromotionProductAdminRead:
    product = await db.get(PromotionProduct, product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(product, key, value)
    await db.flush()
    await log_admin_action(
        db,
        admin_id=admin_user.id,
        action="promotion.product.update",
        entity_type="promotion_product",
        entity_id=product.id,
        details=payload.model_dump(exclude_unset=True),
    )
    await db.commit()
    await db.refresh(product)
    return product


@router.delete("/admin/promotions/products/{product_id}")
async def admin_disable_promotion_product(
    product_id: uuid.UUID,
    admin_user: User = Depends(get_senior_admin_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Soft-disable a product (never delete, purchases may reference it)."""
    product = await db.get(PromotionProduct, product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    product.enabled = False
    await db.flush()
    await log_admin_action(
        db,
        admin_id=admin_user.id,
        action="promotion.product.disable",
        entity_type="promotion_product",
        entity_id=product.id,
    )
    await db.commit()
    return {"message": "Product disabled", "product_id": str(product_id)}


# ---------- Promoted listings management ----------


def _promotion_status(prop: Property, now: datetime) -> str:
    if prop.is_promoted or prop.is_premium:
        if prop.promotion_expires_at and prop.promotion_expires_at < now:
            return "expired"
        return "active"
    return "none"


@router.get("/admin/promotions/listings")
async def admin_list_promoted_listings(
    admin_user: User = Depends(get_senior_admin_user),
    db: AsyncSession = Depends(get_db),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    status_filter: str | None = Query(
        default=None, alias="status", pattern="^(active|expired|none)$"
    ),
    search: str | None = Query(default=None),
) -> dict[str, Any]:
    """List listings with their promotion status and tier."""
    query = select(Property)
    if search:
        query = query.where(Property.title.ilike(f"%{search}%"))
    now = datetime.now(UTC)
    if status_filter == "active":
        query = query.where(
            (Property.is_promoted.is_(True))
            & (
                (Property.promotion_expires_at.is_(None))
                | (Property.promotion_expires_at >= now)
            )
        )
    elif status_filter == "expired":
        query = query.where(
            (Property.is_promoted.is_(True)) & (Property.promotion_expires_at < now)
        )
    elif status_filter == "none":
        query = query.where(
            Property.is_promoted.is_(False) & Property.is_premium.is_(False)
        )

    total = (
        await db.execute(select(func.count()).select_from(query.subquery()))
    ).scalar() or 0
    query = (
        query.order_by(Property.created_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
    )
    props = (await db.execute(query)).scalars().all()

    data = []
    for prop in props:
        tier = prop.promotion_tier or ("premium" if prop.is_premium else None)
        data.append(
            {
                "id": str(prop.id),
                "title": prop.title,
                "reference_code": prop.reference_code,
                "status": (
                    prop.status.value if hasattr(prop.status, "value") else prop.status
                ),
                "tier": tier,
                "is_premium": prop.is_premium,
                "is_promoted": prop.is_promoted,
                "promotion_status": _promotion_status(prop, now),
                "expires_at": (
                    prop.promotion_expires_at.isoformat()
                    if prop.promotion_expires_at
                    else None
                ),
            }
        )

    products = (
        (
            await db.execute(
                select(PromotionProduct).order_by(PromotionProduct.sort_order)
            )
        )
        .scalars()
        .all()
    )
    return {
        "data": data,
        "pagination": {
            "page": page,
            "limit": limit,
            "total": total,
            "pages": (total + limit - 1) // limit,
        },
        "products": [
            {
                "code": p.code,
                "label_az": p.label_az,
                "price": p.price,
                "duration_days": p.duration_days,
                "enabled": p.enabled,
            }
            for p in products
        ],
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

    product = await db.execute(
        select(PromotionProduct).where(PromotionProduct.code == promo.tier)
    )
    product = product.scalar_one_or_none()
    days = promo.days or (product.duration_days if product else 7)
    expiry = datetime.now(UTC) + timedelta(days=days)

    if product is not None:
        prop.is_promoted = True
        prop.is_premium = product.is_premium_tier
    elif promo.tier == "premium":
        prop.is_premium = True
        prop.is_promoted = True
    else:
        prop.is_promoted = True
    prop.promotion_tier = promo.tier
    prop.promotion_expires_at = expiry

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
    prop.promotion_tier = None
    prop.promotion_expires_at = None

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


# ---------- Promotion purchase history ----------


@router.get("/admin/promotions/purchases")
async def admin_list_promotion_purchases(
    admin_user: User = Depends(get_senior_admin_user),
    db: AsyncSession = Depends(get_db),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
) -> dict[str, Any]:
    query = (
        select(PromotionPurchase, PromotionProduct, Property.title)
        .join(PromotionProduct, PromotionProduct.id == PromotionPurchase.product_id)
        .join(Property, Property.id == PromotionPurchase.property_id)
    )
    total = (
        await db.execute(
            select(func.count()).select_from(select(PromotionPurchase.id).subquery())
        )
    ).scalar() or 0
    query = (
        query.order_by(PromotionPurchase.created_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
    )
    rows = (await db.execute(query)).all()
    return {
        "data": [
            {
                "id": str(purchase.id),
                "property_id": str(purchase.property_id),
                "property_title": title,
                "tier": product.code,
                "label": product.label_az,
                "price_paid": purchase.price_paid,
                "status": purchase.status,
                "starts_at": purchase.starts_at.isoformat(),
                "ends_at": purchase.ends_at.isoformat(),
            }
            for purchase, product, title in rows
        ],
        "pagination": {
            "page": page,
            "limit": limit,
            "total": total,
            "pages": (total + limit - 1) // limit,
        },
    }


admin_promotions_router = APIRouter()
admin_promotions_router.include_router(router, prefix="")
