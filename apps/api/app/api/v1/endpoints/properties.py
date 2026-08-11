import uuid
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies.auth import can_edit_property, get_current_user
from app.core.config import get_settings
from app.db.session import get_db
from app.models.enums import PropertyStatus, UserRole
from app.models.property import Property
from app.models.user import User
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

settings = get_settings()

AUTO_PUBLISH_ROLES = (
    UserRole.AGENT,
    UserRole.AGENCY_ADMIN,
    UserRole.MODERATOR,
    UserRole.ADMIN,
    UserRole.SUPER_ADMIN,
)

# Statuses a non-staff owner may set directly via PATCH.
OWNER_ALLOWED_STATUSES = {
    PropertyStatus.DRAFT,
    PropertyStatus.ARCHIVED,
    PropertyStatus.SOLD,
    PropertyStatus.RENTED,
    PropertyStatus.EXPIRED,
}


def _repo(db: AsyncSession) -> PropertyRepository:
    return PropertyRepository(db)


def _now() -> datetime:
    return datetime.now(UTC)


async def _get_property_or_404(
    repo: PropertyRepository, property_id: uuid.UUID
) -> Property:
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


@router.get("/mine", response_model=list[PropertySummaryRead])
async def list_my_properties(
    status_filter: PropertyStatus | None = Query(default=None, alias="status"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[PropertySummaryRead]:
    """The current user's own listings across all statuses (dashboard)."""
    return await _repo(db).list_mine(user.id, status_filter)


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
        400: {"description": "Invalid payload"},
        422: {"description": "Validation error"},
    },
)
async def create_property(
    payload: PropertyCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PropertyRead:
    repo = _repo(db)

    if user.role not in AUTO_PUBLISH_ROLES and payload.status != PropertyStatus.DRAFT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Yalnız qaralama kimi yaradıla bilər. Dərc üçün elanı "
            "təsdiqə göndərin.",
        )
    # Derive ownership from authenticated user; ignore any owner_id in payload.
    payload.owner_id = user.id

    try:
        prop = await repo.create(payload)
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Yaradılma mümkün olmadı: dublikat məlumat ola bilməz.",
        ) from exc
    return repo.to_read(prop)


@router.post(
    "/{property_id}/submit",
    response_model=PropertyRead,
    responses={404: {"description": "Not found"}},
)
async def submit_property(
    property_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PropertyRead:
    """Send a draft to moderation, or publish directly for trusted roles."""
    repo = _repo(db)
    prop = await _get_property_or_404(repo, property_id)
    if not can_edit_property(prop, user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu elanı idarə edə bilməzsiniz",
        )
    if prop.status not in (PropertyStatus.DRAFT, PropertyStatus.REJECTED):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Yalnız qaralama və ya rədd edilmiş elan təsdiqə "
            f"göndərilə bilər (hazırki: {prop.status})",
        )

    auto_publish = user.role in AUTO_PUBLISH_ROLES or user.is_verified
    if auto_publish:
        prop.status = PropertyStatus.ACTIVE.value
        prop.published_at = prop.published_at or _now()
    else:
        prop.status = PropertyStatus.PENDING_REVIEW.value
    await db.commit()
    return repo.to_read(await repo.get_by_id(prop.id))  # type: ignore[arg-type]


@router.patch(
    "/{property_id}",
    response_model=PropertyRead,
    responses={404: {"description": "Not found"}},
)
async def update_property(
    property_id: uuid.UUID,
    payload: PropertyUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PropertyRead:
    repo = _repo(db)
    prop = await _get_property_or_404(repo, property_id)
    if not can_edit_property(prop, user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu elanı redaktə edə bilməzsiniz",
        )
    if (
        payload.status is not None
        and user.role not in AUTO_PUBLISH_ROLES
        and payload.status not in OWNER_ALLOWED_STATUSES
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Statusu birbaşa dəyişə bilməzsiniz — elanı təsdiqə "
            "göndərməlisiniz",
        )
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
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    repo = _repo(db)
    prop = await _get_property_or_404(repo, property_id)
    if not can_edit_property(prop, user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu elanı silə bilməzsiniz",
        )
    await repo.delete(prop)
    await db.commit()
