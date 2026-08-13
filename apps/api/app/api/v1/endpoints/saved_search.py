from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies.auth import get_current_user
from app.db.session import get_db
from app.models.saved_search import SavedSearch
from app.models.user import User
from app.schemas.saved_search import (
    SavedSearchCreate,
    SavedSearchRead,
    SavedSearchUpdate,
)

router = APIRouter(prefix="/saved-searches", tags=["saved-searches"])


@router.get("", response_model=list[SavedSearchRead])
async def list_saved_searches(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    is_active: bool | None = Query(default=None),
) -> list[SavedSearchRead]:
    stmt = select(SavedSearch).where(SavedSearch.user_id == current_user.id)
    if is_active is not None:
        stmt = stmt.where(SavedSearch.is_active == is_active)
    result = await db.execute(stmt)
    searches = result.scalars().all()
    return list(searches)


@router.post("", response_model=SavedSearchRead, status_code=status.HTTP_201_CREATED)
async def create_saved_search(
    payload: SavedSearchCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SavedSearchRead:
    search = SavedSearch(
        user_id=current_user.id,
        name=payload.name,
        filters=payload.filters,
        is_active=payload.is_active,
    )
    db.add(search)
    await db.commit()
    await db.refresh(search)
    return search


@router.patch("/{search_id}", response_model=SavedSearchRead)
async def update_saved_search(
    search_id: uuid.UUID,
    payload: SavedSearchUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SavedSearchRead:
    result = await db.execute(
        select(SavedSearch).where(
            SavedSearch.id == search_id, SavedSearch.user_id == current_user.id
        )
    )
    search = result.scalar_one_or_none()
    if not search:
        raise HTTPException(status_code=404, detail="Saved search not found")
    if payload.name is not None:
        search.name = payload.name
    if payload.filters is not None:
        search.filters = payload.filters
    if payload.is_active is not None:
        search.is_active = payload.is_active
    await db.commit()
    await db.refresh(search)
    return search


@router.delete("/{search_id}", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
async def delete_saved_search(
    search_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    result = await db.execute(
        select(SavedSearch).where(
            SavedSearch.id == search_id, SavedSearch.user_id == current_user.id
        )
    )
    search = result.scalar_one_or_none()
    if not search:
        raise HTTPException(status_code=404, detail="Saved search not found")
    await db.delete(search)
    await db.commit()
