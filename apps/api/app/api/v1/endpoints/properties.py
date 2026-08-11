import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.repositories.property import PropertyRepository
from app.schemas.common import PaginatedResponse
from app.schemas.property import (
    PropertyCreate,
    PropertyQueryParams,
    PropertyRead,
    PropertySummaryRead,
    PropertyUpdate,
)

router = APIRouter(prefix="/properties", tags=["properties"])


def _repo(db: AsyncSession) -> PropertyRepository:
    return PropertyRepository(db)


async def _get_property_or_404(
    repo: PropertyRepository, property_id: uuid.UUID
):
    prop = await repo.get_by_id(property_id)
    if prop is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Elan tapılmadı",
        )
    return prop


@router.get("", response_model=PaginatedResponse[PropertySummaryRead])
async def list_properties(
    params: Annotated[PropertyQueryParams, Query()],
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[PropertySummaryRead]:
    """Search listings with filters, bounding box, sorting and pagination."""
    return await _repo(db).list(params)


@router.get(
    "/{property_id}",
    response_model=PropertyRead,
    responses={404: {"description": "Not found"}},
)
async def get_property(
    property_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> PropertyRead:
    prop = await _get_property_or_404(_repo(db), property_id)
    return _repo(db).to_read(prop)


@router.get(
    "/{property_id}/similar",
    response_model=list[PropertySummaryRead],
)
async def get_similar_properties(
    property_id: uuid.UUID,
    limit: int = Query(default=4, ge=1, le=12),
    db: AsyncSession = Depends(get_db),
) -> list[PropertySummaryRead]:
    repo = _repo(db)
    prop = await _get_property_or_404(repo, property_id)
    return await repo.similar(prop, limit)


@router.post(
    "",
    response_model=PropertyRead,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"description": "Invalid payload (e.g. missing owner)"},
        422: {"description": "Validation error"},
    },
)
async def create_property(
    payload: PropertyCreate,
    db: AsyncSession = Depends(get_db),
) -> PropertyRead:
    repo = _repo(db)
    try:
        prop = await repo.create(payload)
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Yaradılma mümkün olmadı: owner_id mövcud olmalıdır və "
            "dublikat məlumat ola bilməz.",
        ) from exc
    return repo.to_read(prop)


@router.patch(
    "/{property_id}",
    response_model=PropertyRead,
    responses={404: {"description": "Not found"}},
)
async def update_property(
    property_id: uuid.UUID,
    payload: PropertyUpdate,
    db: AsyncSession = Depends(get_db),
) -> PropertyRead:
    repo = _repo(db)
    prop = await _get_property_or_404(repo, property_id)
    try:
        prop = await repo.update(prop, payload)
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Yeniləmə mümkün olmadı: məlumat uyğunsuzluğu var.",
        ) from exc
    return repo.to_read(prop)


@router.delete(
    "/{property_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={404: {"description": "Not found"}},
)
async def delete_property(
    property_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> None:
    repo = _repo(db)
    prop = await _get_property_or_404(repo, property_id)
    await repo.delete(prop)
    await db.commit()
