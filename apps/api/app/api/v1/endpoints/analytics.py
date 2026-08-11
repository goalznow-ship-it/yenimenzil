from __future__ import annotations

import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies.auth import get_current_user, get_optional_user
from app.db.session import get_db
from app.models.analytics import AnalyticsEvent
from app.schemas.analytics import AnalyticsEventRead
from app.models.enums import UserRole

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/events", response_model=List[AnalyticsEventRead])
async def list_analytics_events(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    event_type: str | None = Query(default=None),
    property_id: uuid.UUID | None = Query(default=None),
    user_id: uuid.UUID | None = Query(default=None),
) -> List[AnalyticsEventRead]:
    # Only moderators can view analytics
    if current_user.role not in (UserRole.MODERATOR, UserRole.ADMIN, UserRole.SUPER_ADMIN):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    stmt = select(AnalyticsEvent).order_by(AnalyticsEvent.created_at.desc())
    if event_type:
        stmt = stmt.where(AnalyticsEvent.event_type == event_type)
    if property_id:
        stmt = stmt.where(AnalyticsEvent.property_id == property_id)
    if user_id:
        stmt = stmt.where(AnalyticsEvent.user_id == user_id)
    stmt = stmt.offset(offset).limit(limit)
    result = await db.execute(stmt)
    events = result.scalars().all()
    return list(events)


# Internal endpoint for creating analytics events (used by other services)
@router.post("/events", response_model=AnalyticsEventRead, status_code=status.HTTP_201_CREATED)
async def create_analytics_event(
    payload: dict,
    current_user: User = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
) -> AnalyticsEventRead:
    # For simplicity, expect payload with required fields
    event = AnalyticsEvent(
        user_id=current_user.id if current_user else None,
        property_id=payload.get("property_id"),
        event_type=payload["event_type"],
        payload=payload.get("payload", {}),
        ip_address=payload.get("ip_address"),
        user_agent=payload.get("user_agent"),
    )
    db.add(event)
    await db.commit()
    await db.refresh(event)
    return event
