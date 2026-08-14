from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies.auth import get_current_user
from app.db.session import get_db
from app.models.enums import UserRole
from app.models.property import Property, PropertyPriceHistory
from app.models.user import User
from app.schemas.property import PropertyPriceHistoryRead

router = APIRouter(prefix="/price-history", tags=["price-history"])


@router.get("/{property_id}", response_model=list[PropertyPriceHistoryRead])
async def get_property_price_history(
    property_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[PropertyPriceHistoryRead]:
    prop = await db.get(Property, property_id)
    if prop is None:
        raise HTTPException(status_code=404, detail="Property not found")
    is_staff = current_user.role in (
        UserRole.MODERATOR,
        UserRole.ADMIN,
        UserRole.SUPER_ADMIN,
    )
    if prop.owner_id != current_user.id and not is_staff:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Price history is only available to the listing owner",
        )
    result = await db.execute(
        select(PropertyPriceHistory)
        .where(PropertyPriceHistory.property_id == property_id)
        .order_by(PropertyPriceHistory.recorded_at)
    )
    history = result.scalars().all()
    return list(history)
