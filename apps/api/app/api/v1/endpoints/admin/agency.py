from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies.auth import get_current_user
from app.db.session import get_db
from app.models.agency import Agency, Agent
from app.models.enums import UserRole
from app.models.property import Property
from app.models.user import User
from app.schemas.agency import AgencyRead
from app.services.admin_log import log_admin_action


# Schema for admin agency update
class AdminAgencyUpdate(BaseModel):
    name: str | None = Field(None, min_length=2, max_length=200)
    slug: str | None = Field(None, min_length=2, max_length=220)
    email: str | None = Field(None, max_length=255)
    phone: str | None = Field(None, max_length=32)
    website: str | None = Field(None, max_length=500)
    logo_url: str | None = Field(None, max_length=500)
    description: str | None = Field(None, max_length=1000)
    is_verified: bool | None = None

router = APIRouter(tags=["admin-agencies"])


# Dependency to check for admin/moderator/super_admin access
def get_admin_user(
    current_user: User = Depends(get_current_user),
) -> User:
    if current_user.role not in (UserRole.MODERATOR, UserRole.ADMIN, UserRole.SUPER_ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )
    return current_user


@router.get("/admin/agencies")
async def admin_list_agencies(
    admin_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
    # Pagination
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    # Search
    search: str | None = Query(default=None),
    # Filters
    is_verified: bool | None = Query(default=None),
    # Date range
    created_after: datetime | None = Query(default=None),
    created_before: datetime | None = Query(default=None),
    # Sorting
    sort_by: str = Query(default="created_at", pattern="^(created_at|name)$"),
    sort_order: str = Query(default="desc", pattern="^(asc|desc)$"),
) -> dict[str, Any]:
    """Admin endpoint to list agencies with filtering, search, and pagination."""
    
    # Base query
    query = select(Agency)
    
    # Apply search
    if search:
        search_term = f"%{search}%"
        query = query.where(
            or_(
                Agency.name.ilike(search_term),
                Agency.description.ilike(search_term),
            )
        )
    
    # Apply filters
    if is_verified is not None:
        query = query.where(Agency.is_verified == is_verified)
    if created_after:
        query = query.where(Agency.created_at >= created_after)
    if created_before:
        query = query.where(Agency.created_at <= created_before)
    
    # Apply sorting
    if sort_order == "asc":
        query = query.order_by(getattr(Agency, sort_by).asc())
    else:
        query = query.order_by(getattr(Agency, sort_by).desc())
    
    # Get total count for pagination
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    # Apply pagination
    offset = (page - 1) * limit
    query = query.offset(offset).limit(limit)
    
    # Execute query
    result = await db.execute(query)
    agencies = result.scalars().all()
    
    # Format response
    agency_list = []
    for agency in agencies:
        agency_list.append({
            "id": str(agency.id),
            "name": agency.name,
            "slug": agency.slug,
            "email": agency.email,
            "phone": agency.phone,
            "website": agency.website,
            "logo_url": agency.logo_url,
            "description": agency.description,
            "is_verified": agency.is_verified,
            "created_at": agency.created_at.isoformat() if agency.created_at else None,
            "updated_at": agency.updated_at.isoformat() if agency.updated_at else None,
        })
    
    return {
        "data": agency_list,
        "pagination": {
            "page": page,
            "limit": limit,
            "total": total,
            "pages": (total + limit - 1) // limit,
        },
        "filters": {
            "is_verified": [True, False],
        }
    }


@router.get("/admin/agencies/{agency_id}")
async def admin_get_agency(
    agency_id: uuid.UUID,
    admin_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
) -> AgencyRead:
    """Get a specific agency's details."""
    agency = await db.get(Agency, agency_id)
    if not agency:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agency not found",
        )
    return AgencyRead.model_validate(agency)


@router.patch("/admin/agencies/{agency_id}")
async def admin_update_agency(
    agency_id: uuid.UUID,
    agency_update: AdminAgencyUpdate,
    admin_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
) -> AgencyRead:
    """Update an agency's details."""
    agency = await db.get(Agency, agency_id)
    if not agency:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agency not found",
        )
    
    # Update agency fields if provided
    update_data = agency_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(agency, field):
            setattr(agency, field, value)
    
    await db.flush()
    await log_admin_action(
        db,
        admin_id=admin_user.id,
        action="agency.update",
        entity_type="agency",
        entity_id=agency_id,
        details=update_data,
    )
    await db.commit()
    await db.refresh(agency)
    return AgencyRead.model_validate(agency)


@router.delete("/admin/agencies/{agency_id}")
async def admin_delete_agency(
    agency_id: uuid.UUID,
    admin_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Deactivate an agency (set is_verified to False)."""
    agency = await db.get(Agency, agency_id)
    if not agency:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agency not found",
        )
    
    # Deactivate the agency instead of deleting to preserve data integrity
    agency.is_verified = False
    await db.flush()
    await log_admin_action(
        db,
        admin_id=admin_user.id,
        action="agency.deactivate",
        entity_type="agency",
        entity_id=agency_id,
    )
    await db.commit()
    
    return {
        "message": "Agency deactivated successfully",
        "agency_id": str(agency_id),
    }


@router.get("/admin/agents/reputation")
async def admin_agent_reputation(
    admin_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    search: str | None = Query(default=None),
) -> dict[str, Any]:
    """Agent reputation foundation: a transparent 0-100 score derived from
    real, verifiable signals only (identity/phone verification, listing
    activity, record health). Formula documented in the response."""
    from sqlalchemy import func as sa_func

    query = select(Agent)
    if search:
        query = query.where(
            or_(Agent.name.ilike(f"%{search}%"), Agent.email.ilike(f"%{search}%"))
        )
    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar() or 0
    agents = (await db.execute(query.order_by(Agent.created_at.desc()).offset((page - 1) * limit).limit(limit))).scalars().all()

    data = []
    for agent in agents:
        stats = await db.execute(
            select(
                sa_func.count(Property.id),
                sa_func.sum(Property.views),
            ).where(Property.agent_id == agent.id)
        )
        listing_count, total_views = stats.one()
        active_count = (
            await db.execute(
                select(sa_func.count(Property.id)).where(
                    Property.agent_id == agent.id, Property.status == "active"
                )
            )
        ).scalar() or 0

        score = 50
        if agent.verified_identity:
            score += 10
        if agent.verified_phone:
            score += 10
        score += min(listing_count or 0, 15)
        score += min(active_count or 0, 10)
        if total_views:
            score += min(round((total_views or 0) / max(listing_count or 1, 1) / 10), 5)
        score = min(100, score)

        data.append({
            "id": str(agent.id),
            "name": agent.name,
            "email": agent.email,
            "phone": agent.phone,
            "agency_id": str(agent.agency_id) if agent.agency_id else None,
            "verified_identity": agent.verified_identity,
            "verified_phone": agent.verified_phone,
            "listing_count": listing_count or 0,
            "active_listings": active_count,
            "total_views": total_views or 0,
            "reputation_score": score,
        })

    return {
        "data": data,
        "pagination": {"page": page, "limit": limit, "total": total, "pages": (total + limit - 1) // limit},
        "formula": "base 50 + identity(10) + phone(10) + listings(<=15) + active(<=10) + views signal(<=5), capped at 100",
    }


# Create the main admin router for agencies
admin_agencies_router = APIRouter()
admin_agencies_router.include_router(router, prefix="")