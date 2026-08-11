from __future__ import annotations

import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies.auth import get_current_user, require_roles
from app.db.session import get_db
from app.models.agency import Agency
from app.schemas.agency import AgencyCreate, AgencyRead, AgencyUpdate
from app.models.user import User
from app.models.enums import UserRole

router = APIRouter(prefix="/agencies", tags=["agencies"])


def _require_admin_or_above(user: User) -> User:
    if user.role not in (UserRole.ADMIN, UserRole.SUPER_ADMIN):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    return user


@router.get("", response_model=List[AgencyRead])
async def list_agencies(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
) -> List[AgencyRead]:
    # For now, allow any authenticated user to list agencies
    stmt = select(Agency).offset(offset).limit(limit)
    result = await db.execute(stmt)
    agencies = result.scalars().all()
    return list(agencies)


@router.post("", response_model=AgencyRead, status_code=status.HTTP_201_CREATED)
async def create_agency(
    payload: AgencyCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AgencyRead:
    # Only admins can create agencies
    _require_admin_or_above(current_user)
    agency = Agency(**payload.model_dump())
    db.add(agency)
    await db.commit()
    await db.refresh(agency)
    return agency


@router.get("/{agency_id}", response_model=AgencyRead)
async def get_agency(
    agency_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AgencyRead:
    result = await db.execute(select(Agency).where(Agency.id == agency_id))
    agency = result.scalar_one_or_none()
    if not agency:
        raise HTTPException(status_code=404, detail="Agency not found")
    return agency


@router.patch("/{agency_id}", response_model=AgencyRead)
async def update_agency(
    agency_id: uuid.UUID,
    payload: AgencyUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AgencyRead:
    _require_admin_or_above(current_user)
    result = await db.execute(select(Agency).where(Agency.id == agency_id))
    agency = result.scalar_one_or_none()
    if not agency:
        raise HTTPException(status_code=404, detail="Agency not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(agency, field, value)
    await db.commit()
    await db.refresh(agency)
    return agency


@router.delete("/{agency_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_agency(
    agency_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    _require_admin_or_above(current_user)
    result = await db.execute(select(Agency).where(Agency.id == agency_id))
    agency = result.scalar_one_or_none()
    if not agency:
        raise HTTPException(status_code=404, detail="Agency not found")
    await db.delete(agency)
    await db.commit()
