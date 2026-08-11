from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies.auth import get_current_user
from app.db.session import get_db
from app.models.property import PropertyPriceHistory
from app.models.user import User
from app.schemas.property import PropertyPriceHistoryRead

router = APIRouter(prefix="/price-history", tags=["price-history"])


@router.get("/{property_id}", response_model=list[PropertyPriceHistoryRead])
async def get_property_price_history(
    property_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[PropertyPriceHistoryRead]:
    # Check if property exists and user has permission to view it (at least view)
    # For now, we allow any authenticated user to view price history of any property?
    # In reality, we might want to restrict to owner or agent, but for simplicity we allow.
    result = await db.execute(
        select(PropertyPriceHistory)
        .where(PropertyPriceHistory.property_id == property_id)
        .order_by(PropertyPriceHistory.recorded_at)
    )
    history = result.scalars().all()
    return list(history)
