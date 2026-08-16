from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies.auth import get_current_user
from app.db.session import get_db
from app.models.analytics import AnalyticsEvent
from app.models.enums import AnalyticsEventType
from app.models.favorite import Favorite, FavoriteCollection
from app.models.property import Property
from app.models.user import User
from app.repositories.property import PropertyRepository, _summary_load_options
from app.schemas.favorite import (
    FavoriteCollectionCreate,
    FavoriteCollectionRead,
    FavoriteCollectionUpdate,
    FavoriteUpdate,
)
from app.schemas.property import PropertyRead

router = APIRouter(prefix="/favorites", tags=["favorites"])


async def _collection_or_default(
    db: AsyncSession, user_id: uuid.UUID, collection_id: uuid.UUID | None
) -> None:
    if collection_id is None:
        return
    result = await db.execute(
        select(FavoriteCollection).where(
            FavoriteCollection.id == collection_id,
            FavoriteCollection.user_id == user_id,
        )
    )
    if result.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="Collection not found")


async def _log_event(
    db: AsyncSession, user: User, property_id: uuid.UUID, event_type: AnalyticsEventType
) -> None:
    db.add(
        AnalyticsEvent(
            user_id=user.id,
            property_id=property_id,
            event_type=event_type.value,
        )
    )


# ---------------------------------------------------------------------------
# Collections (folders)
# ---------------------------------------------------------------------------


@router.get("/collections", response_model=list[FavoriteCollectionRead])
async def list_collections(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[FavoriteCollectionRead]:
    rows = (
        await db.execute(
            select(
                FavoriteCollection,
                func.count(Favorite.id).label("favorite_count"),
            )
            .outerjoin(Favorite, Favorite.collection_id == FavoriteCollection.id)
            .where(FavoriteCollection.user_id == current_user.id)
            .group_by(FavoriteCollection.id)
            .order_by(
                FavoriteCollection.is_default.desc(), FavoriteCollection.created_at
            )
        )
    ).all()
    return [
        FavoriteCollectionRead(
            id=c.id,
            name=c.name,
            is_default=c.is_default,
            created_at=c.created_at,
            favorite_count=count,
        )
        for c, count in rows
    ]


@router.post(
    "/collections",
    response_model=FavoriteCollectionRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_collection(
    payload: FavoriteCollectionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> FavoriteCollectionRead:
    result = await db.execute(
        select(FavoriteCollection).where(
            FavoriteCollection.user_id == current_user.id,
            func.lower(FavoriteCollection.name) == payload.name.strip().lower(),
        )
    )
    if result.scalar_one_or_none() is not None:
        raise HTTPException(status_code=409, detail="Collection already exists")
    collection = FavoriteCollection(user_id=current_user.id, name=payload.name.strip())
    db.add(collection)
    await db.commit()
    await db.refresh(collection)
    return FavoriteCollectionRead(
        id=collection.id,
        name=collection.name,
        is_default=collection.is_default,
        created_at=collection.created_at,
        favorite_count=0,
    )


@router.patch("/collections/{collection_id}", response_model=FavoriteCollectionRead)
async def rename_collection(
    collection_id: uuid.UUID,
    payload: FavoriteCollectionUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> FavoriteCollectionRead:
    collection = await db.get(FavoriteCollection, collection_id)
    if collection is None or collection.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Collection not found")
    if collection.is_default:
        raise HTTPException(
            status_code=400, detail="Default collection cannot be renamed"
        )
    collection.name = payload.name.strip()
    await db.commit()
    await db.refresh(collection)
    return FavoriteCollectionRead(
        id=collection.id,
        name=collection.name,
        is_default=collection.is_default,
        created_at=collection.created_at,
        favorite_count=0,
    )


@router.delete(
    "/collections/{collection_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
)
async def delete_collection(
    collection_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    collection = await db.get(FavoriteCollection, collection_id)
    if collection is None or collection.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Collection not found")
    if collection.is_default:
        raise HTTPException(
            status_code=400, detail="Default collection cannot be deleted"
        )
    # Favorites fall back to the default list (SET NULL).
    await db.delete(collection)
    await db.commit()


# ---------------------------------------------------------------------------
# Favorites
# ---------------------------------------------------------------------------


@router.get("", response_model=list[PropertyRead])
async def list_favorites(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    collection_id: uuid.UUID | None = Query(default=None),
) -> list[PropertyRead]:
    stmt = (
        select(Property)
        .options(*_summary_load_options())
        .join(Favorite, Favorite.property_id == Property.id)
        .where(Favorite.user_id == current_user.id)
        .order_by(Favorite.created_at.desc())
    )
    if collection_id is not None:
        await _collection_or_default(db, current_user.id, collection_id)
        stmt = stmt.where(Favorite.collection_id == collection_id)
    else:
        # Default view: the unassigned (default) list
        stmt = stmt.where(Favorite.collection_id.is_(None))
    result = await db.execute(stmt)
    properties = result.scalars().all()
    repo = PropertyRepository(db)
    return [repo.to_read(prop) for prop in properties]


@router.post("/{property_id}", status_code=status.HTTP_201_CREATED)
async def add_favorite(
    property_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    payload: FavoriteUpdate | None = None,
) -> None:
    result = await db.execute(select(Property).where(Property.id == property_id))
    property = result.scalar_one_or_none()
    if not property:
        raise HTTPException(status_code=404, detail="Property not found")
    await _collection_or_default(
        db, current_user.id, payload.collection_id if payload else None
    )
    result = await db.execute(
        select(Favorite).where(
            Favorite.user_id == current_user.id, Favorite.property_id == property_id
        )
    )
    existing = result.scalar_one_or_none()
    if existing:
        if payload and payload.collection_id != existing.collection_id:
            existing.collection_id = payload.collection_id
            await db.commit()
        return  # Already favorited, do nothing
    favorite = Favorite(
        user_id=current_user.id,
        property_id=property_id,
        collection_id=payload.collection_id if payload else None,
    )
    db.add(favorite)
    await _log_event(
        db, current_user, property_id, AnalyticsEventType.PROPERTY_FAVORITE
    )
    await db.commit()


@router.patch("/{property_id}", response_model=None)
async def move_favorite(
    property_id: uuid.UUID,
    payload: FavoriteUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    await _collection_or_default(db, current_user.id, payload.collection_id)
    result = await db.execute(
        select(Favorite).where(
            Favorite.user_id == current_user.id, Favorite.property_id == property_id
        )
    )
    favorite = result.scalar_one_or_none()
    if not favorite:
        raise HTTPException(status_code=404, detail="Favorite not found")
    favorite.collection_id = payload.collection_id
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
    await _log_event(
        db, current_user, property_id, AnalyticsEventType.PROPERTY_UNFAVORITE
    )
    await db.commit()
