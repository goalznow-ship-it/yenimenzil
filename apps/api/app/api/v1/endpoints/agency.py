from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies.auth import get_current_user, get_optional_user
from app.db.session import get_db
from app.models.agency import Agency, Agent
from app.models.enums import UserRole
from app.models.user import User
from app.repositories.property import PropertyRepository
from app.schemas.agency import AgencyCreate, AgencyRead, AgencyUpdate
from app.schemas.agent import AgentRead
from app.schemas.property import PropertyQueryParams

router = APIRouter(prefix="/agencies", tags=["agencies"])


def _require_admin_or_above(user: User) -> User:
    if user.role not in (UserRole.ADMIN, UserRole.SUPER_ADMIN):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    return user


@router.get("", response_model=list[AgencyRead])
async def list_agencies(
    db: AsyncSession = Depends(get_db),
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
) -> list[AgencyRead]:
    stmt = select(Agency).order_by(Agency.is_verified.desc(), Agency.name).offset(offset).limit(limit)
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


@router.get("/{agency_id}/public", response_model=dict)
async def get_agency_public_profile(
    agency_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_optional_user),
) -> dict:
    """Public agency profile with its active listings and agents."""
    result = await db.execute(select(Agency).where(Agency.id == agency_id))
    agency = result.scalar_one_or_none()
    if not agency:
        raise HTTPException(status_code=404, detail="Agency not found")

    params = PropertyQueryParams(agency_id=agency_id, page=1, page_size=24)
    listings = await PropertyRepository(db).list(params)
    agents_result = await db.execute(select(Agent).where(Agent.agency_id == agency_id))
    agents = agents_result.scalars().all()
    return {
        "agency": AgencyRead.model_validate(agency),
        "listings": listings,
        "agents": [AgentRead.model_validate(a) for a in agents],
        "is_favorite": False,
    }


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


@router.delete(
    "/{agency_id}", status_code=status.HTTP_204_NO_CONTENT, response_model=None
)
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
