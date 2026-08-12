from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies.auth import get_current_user
from app.db.session import get_db
from app.models.enums import UserRole
from app.models.property import Property, PropertyLocation
from app.models.user import User

router = APIRouter(tags=["admin-locations"])


def get_admin_user(
    current_user: User = Depends(get_current_user),
) -> User:
    if current_user.role not in (UserRole.MODERATOR, UserRole.ADMIN, UserRole.SUPER_ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )
    return current_user


@router.get("/admin/locations")
async def admin_location_overview(
    admin_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Aggregate location usage across listings: cities and districts with counts."""
    city_rows = await db.execute(
        select(PropertyLocation.city, func.count(Property.id))
        .join(Property, Property.id == PropertyLocation.property_id)
        .where(PropertyLocation.city.is_not(None))
        .group_by(PropertyLocation.city)
        .order_by(func.count(Property.id).desc())
    )
    cities = [
        {"name": city, "listings": count}
        for city, count in city_rows.all()
    ]

    district_rows = await db.execute(
        select(PropertyLocation.district, func.count(Property.id))
        .join(Property, Property.id == PropertyLocation.property_id)
        .where(PropertyLocation.district.is_not(None))
        .group_by(PropertyLocation.district)
        .order_by(func.count(Property.id).desc())
    )
    districts = [
        {"name": district, "listings": count}
        for district, count in district_rows.all()
    ]

    metro_rows = await db.execute(
        select(PropertyLocation.metro, func.count(Property.id))
        .join(Property, Property.id == PropertyLocation.property_id)
        .where(PropertyLocation.metro.is_not(None))
        .group_by(PropertyLocation.metro)
        .order_by(func.count(Property.id).desc())
    )
    metros = [
        {"name": metro, "listings": count}
        for metro, count in metro_rows.all()
    ]

    return {
        "cities": cities,
        "districts": districts,
        "metros": metros,
        "unlocated": (
            await db.execute(
                select(func.count(Property.id)).where(
                    ~select(PropertyLocation.property_id).exists()
                )
            )
        ).scalar()
        or 0,
    }


admin_locations_router = APIRouter()
admin_locations_router.include_router(router, prefix="")