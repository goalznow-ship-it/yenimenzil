"""Residential complex endpoints (Phase 14): new-build developments."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies.auth import get_current_user, get_optional_user
from app.db.session import get_db
from app.models.complex import ResidentialComplex
from app.models.enums import PropertyStatus, UserRole
from app.models.property import Property
from app.models.user import User
from app.repositories.property import PropertyRepository, _summary_load_options
from app.schemas.complex import (
    ResidentialComplexCreate,
    ResidentialComplexDetail,
    ResidentialComplexRead,
    ResidentialComplexUpdate,
)

router = APIRouter(prefix="/complexes", tags=["complexes"])


def _require_staff(user: User) -> User:
    if user.role not in (UserRole.MODERATOR, UserRole.ADMIN, UserRole.SUPER_ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )
    return user


async def _get_complex_or_404(
    db: AsyncSession, complex_id: uuid.UUID
) -> ResidentialComplex:
    complex_row = await db.get(ResidentialComplex, complex_id)
    if complex_row is None:
        raise HTTPException(status_code=404, detail="Kompleks tapılmadı")
    return complex_row


async def _counts(db: AsyncSession, complex_row: ResidentialComplex) -> tuple[int, int]:
    props = (
        (
            await db.execute(
                select(Property).where(Property.complex_id == complex_row.id)
            )
        )
        .scalars()
        .all()
    )
    active = [p for p in props if p.status == PropertyStatus.ACTIVE.value]
    units_available = int(sum(p.rooms or 0 for p in active)) if active else 0
    return len(props), units_available


def _to_read(
    complex_row: ResidentialComplex, properties_count: int, units_available: int
) -> ResidentialComplexRead:
    return ResidentialComplexRead(
        id=complex_row.id,
        name=complex_row.name,
        slug=complex_row.slug,
        developer_name=complex_row.developer_name,
        status=complex_row.status,
        description=complex_row.description,
        address_text=complex_row.address_text,
        city=complex_row.city,
        district=complex_row.district,
        metro=complex_row.metro,
        latitude=complex_row.latitude,
        longitude=complex_row.longitude,
        completion_year=complex_row.completion_year,
        total_units=complex_row.total_units,
        cover_image=complex_row.cover_image,
        amenities=complex_row.amenities or [],
        is_verified=complex_row.is_verified,
        properties_count=properties_count,
        units_available=units_available,
        created_at=complex_row.created_at,
        updated_at=complex_row.updated_at,
    )


@router.get("", response_model=list[ResidentialComplexRead])
async def list_complexes(
    db: AsyncSession = Depends(get_db),
    city: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> list[ResidentialComplexRead]:
    """Public list of residential complexes."""
    stmt = select(ResidentialComplex).order_by(ResidentialComplex.created_at.desc())
    if city:
        stmt = stmt.where(ResidentialComplex.city == city)
    if status_filter:
        stmt = stmt.where(ResidentialComplex.status == status_filter)
    rows = (await db.execute(stmt.offset(offset).limit(limit))).scalars().all()
    result: list[ResidentialComplexRead] = []
    for row in rows:
        count, units = await _counts(db, row)
        result.append(_to_read(row, count, units))
    return result


@router.get("/{complex_id}", response_model=ResidentialComplexDetail)
async def get_complex(
    complex_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_optional_user),
) -> ResidentialComplexDetail:
    """Public detail page with the complex's active listings."""
    complex_row = await _get_complex_or_404(db, complex_id)
    count, units = await _counts(db, complex_row)

    repo = PropertyRepository(db)
    stmt = (
        select(Property)
        .where(
            Property.complex_id == complex_id,
            Property.status == PropertyStatus.ACTIVE.value,
        )
        .order_by(Property.created_at.desc())
        .limit(48)
        .options(*_summary_load_options())
    )
    rows = (await db.execute(stmt)).scalars().all()
    properties = [repo._to_summary_read(p) for p in rows]

    base = _to_read(complex_row, count, units)
    return ResidentialComplexDetail(
        **base.model_dump(),
        properties=properties,
    )


@router.post(
    "", response_model=ResidentialComplexRead, status_code=status.HTTP_201_CREATED
)
async def create_complex(
    payload: ResidentialComplexCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ResidentialComplexRead:
    """Create a complex (staff only)."""
    _require_staff(current_user)
    complex_row = ResidentialComplex(**payload.model_dump())
    db.add(complex_row)
    await db.commit()
    await db.refresh(complex_row)
    return _to_read(complex_row, 0, 0)


@router.patch("/{complex_id}", response_model=ResidentialComplexRead)
async def update_complex(
    complex_id: uuid.UUID,
    payload: ResidentialComplexUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ResidentialComplexRead:
    _require_staff(current_user)
    complex_row = await _get_complex_or_404(db, complex_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(complex_row, field, value)
    await db.commit()
    await db.refresh(complex_row)
    count, units = await _counts(db, complex_row)
    return _to_read(complex_row, count, units)


@router.delete("/{complex_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_complex(
    complex_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    _require_staff(current_user)
    complex_row = await _get_complex_or_404(db, complex_id)
    await db.delete(complex_row)
    await db.commit()
