from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies.auth import get_current_user
from app.db.session import get_db
from app.models.favorite import Favorite
from app.models.property import Property
from app.models.user import User
from app.schemas.property import PropertyRead

router = APIRouter(prefix="/favorites", tags=["favorites"])


@router.get("", response_model=list[PropertyRead])
async def list_favorites(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[PropertyRead]:
    stmt = (
        select(Property)
        .join(Favorite, Favorite.property_id == Property.id)
        .where(Favorite.user_id == current_user.id)
    )
    result = await db.execute(stmt)
    properties = result.scalars().all()
    return [PropertyRead.model_validate(prop) for prop in properties]


@router.post("/{property_id}", status_code=status.HTTP_201_CREATED)
async def add_favorite(
    property_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    # Check if property exists
    result = await db.execute(select(Property).where(Property.id == property_id))
    property = result.scalar_one_or_none()
    if not property:
        raise HTTPException(status_code=404, detail="Property not found")
    # Check if already favorited
    result = await db.execute(
        select(Favorite).where(
            Favorite.user_id == current_user.id, Favorite.property_id == property_id
        )
    )
    existing = result.scalar_one_or_none()
    if existing:
        return  # Already favorited, do nothing
    favorite = Favorite(user_id=current_user.id, property_id=property_id)
    db.add(favorite)
    await db.commit()


@router.delete(
    "/{property_id}", status_code=status.HTTP_204_NO_CONTENT, response_model=None
)
async def remove_favorite(
    property_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    result = await db.execute(
        select(Favorite).where(
            Favorite.user_id == current_user.id, Favorite.property_id == property_id
        )
    )
    favorite = result.scalar_one_or_none()
    if not favorite:
        raise HTTPException(status_code=404, detail="Favorite not found")
    await db.delete(favorite)
    await db.commit()
