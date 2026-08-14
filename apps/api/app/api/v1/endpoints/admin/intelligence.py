from __future__ import annotations

import uuid
from statistics import median
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies.auth import get_current_user
from app.db.session import get_db
from app.models.enums import DealType, PropertyType, UserRole
from app.models.property import Property, PropertyLocation
from app.models.user import User

router = APIRouter(tags=["admin-intelligence"])


def get_admin_user(
    current_user: User = Depends(get_current_user),
) -> User:
    if current_user.role not in (
        UserRole.MODERATOR,
        UserRole.ADMIN,
        UserRole.SUPER_ADMIN,
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )
    return current_user


def _status_value(status) -> str:
    return status.value if hasattr(status, "value") else str(status)


@router.get("/admin/price-intelligence")
async def admin_price_intelligence(
    admin_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
    deal_type: DealType | None = Query(default=None),
    property_type: PropertyType | None = Query(default=None),
    city: str | None = Query(default=None),
    district: str | None = Query(default=None),
) -> dict[str, Any]:
    """Price intelligence: median/avg price and price per m2 by district/city.

    Only ACTIVE listings are considered so the stats reflect the live market.
    """
    query = (
        select(
            PropertyLocation.city,
            PropertyLocation.district,
            Property.price,
            Property.area_total,
        )
        .join(PropertyLocation, PropertyLocation.property_id == Property.id)
        .where(Property.status == "active")
    )
    if deal_type:
        query = query.where(Property.deal_type == deal_type)
    if property_type:
        query = query.where(Property.property_type == property_type)
    if city:
        query = query.where(PropertyLocation.city == city)
    if district:
        query = query.where(PropertyLocation.district == district)

    rows = (await db.execute(query)).all()

    groups: dict[tuple, list[tuple[float, float]]] = {}
    for row in rows:
        if row.price is None or row.area_total is None or float(row.area_total) <= 0:
            continue
        key = (row.city, row.district)
        groups.setdefault(key, []).append((float(row.price), float(row.area_total)))

    def summarize(items: list[tuple[float, float]]) -> dict[str, Any]:
        prices = [p for p, _ in items]
        per_m2 = [p / a for p, a in items]
        return {
            "count": len(items),
            "avg_price": round(sum(prices) / len(prices), 2),
            "median_price": round(median(prices), 2),
            "min_price": round(min(prices), 2),
            "max_price": round(max(prices), 2),
            "avg_price_per_m2": round(sum(per_m2) / len(per_m2), 2),
            "median_price_per_m2": round(median(per_m2), 2),
        }

    return {
        "deal_type": deal_type.value if deal_type else "all",
        "property_type": property_type.value if property_type else "all",
        "segments": [
            {"city": city, "district": district, **summarize(items)}
            for (city, district), items in sorted(
                groups.items(), key=lambda kv: -kv[1][0][0]
            )
        ],
        "note": "Based on active listings only",
    }


@router.get("/admin/listings/{property_id}/comparables")
async def admin_comparable_listings(
    property_id: uuid.UUID,
    admin_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(default=10, ge=1, le=50),
) -> dict[str, Any]:
    """Comparable listings for a given property (same market segment)."""
    prop = await db.get(Property, property_id)
    if not prop:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Listing not found",
        )

    location = (
        await db.execute(
            select(PropertyLocation).where(PropertyLocation.property_id == property_id)
        )
    ).scalar_one_or_none()

    query = (
        select(Property, PropertyLocation)
        .join(PropertyLocation, PropertyLocation.property_id == Property.id)
        .where(Property.id != property_id)
        .where(Property.status.in_(["active", "pending_review"]))
        .where(Property.deal_type == prop.deal_type)
        .where(Property.property_type == prop.property_type)
    )
    if location:
        where_parts = []
        if location.city:
            where_parts.append(PropertyLocation.city == location.city)
        if location.district:
            where_parts.append(PropertyLocation.district == location.district)
        if where_parts:
            query = query.where(or_(*where_parts))
        # Rooms: within ±1 if known
        if prop.rooms:
            query = query.where(
                Property.rooms.between(max(prop.rooms - 1, 0), prop.rooms + 1)
            )
        # Area: within ±20%
        if prop.area_total and float(prop.area_total) > 0:
            area = float(prop.area_total)
            query = query.where(Property.area_total.between(area * 0.8, area * 1.2))

    rows = (await db.execute(query.limit(limit))).all()
    comparables = []
    for other, other_loc in rows:
        price = float(other.price) if other.price is not None else None
        area = float(other.area_total) if other.area_total is not None else None
        comparables.append(
            {
                "id": str(other.id),
                "title": other.title,
                "reference_code": other.reference_code,
                "price": price,
                "price_per_m2": round(price / area, 2) if price and area else None,
                "rooms": other.rooms,
                "area_total": area,
                "status": _status_value(other.status),
                "city": other_loc.city,
                "district": other_loc.district,
                "views": other.views,
                "created_at": other.created_at.isoformat()
                if other.created_at
                else None,
            }
        )

    # Price position of the target property among comparables
    prices = [c["price"] for c in comparables if c["price"] is not None]
    target_price = float(prop.price) if prop.price is not None else None
    percentile = None
    if prices and target_price is not None:
        sorted_prices = sorted(prices)
        below = sum(1 for p in sorted_prices if p <= target_price)
        percentile = round(below / len(sorted_prices) * 100, 1)

    return {
        "property_id": str(property_id),
        "reference_code": prop.reference_code,
        "target_price": target_price,
        "target_price_per_m2": (
            round(target_price / float(prop.area_total), 2)
            if target_price and prop.area_total and float(prop.area_total) > 0
            else None
        ),
        "comparable_count": len(comparables),
        "price_percentile": percentile,
        "comparables": comparables,
        "criteria": {
            "deal_type": prop.deal_type.value
            if hasattr(prop.deal_type, "value")
            else prop.deal_type,
            "property_type": prop.property_type.value
            if hasattr(prop.property_type, "value")
            else prop.property_type,
            "city": location.city if location else None,
            "district": location.district if location else None,
            "rooms_tolerance": 1,
            "area_tolerance_pct": 20,
        },
    }


admin_intelligence_router = APIRouter()
admin_intelligence_router.include_router(router, prefix="")
