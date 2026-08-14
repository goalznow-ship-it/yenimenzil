from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies.auth import get_current_user, get_optional_user
from app.db.session import get_db
from app.models.analytics import AnalyticsEvent
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.analytics import (
    AnalyticsEventCreate,
    AnalyticsEventRead,
    PopularSearchRead,
)

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/events", response_model=list[AnalyticsEventRead])
async def list_analytics_events(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    event_type: str | None = Query(default=None),
    property_id: uuid.UUID | None = Query(default=None),
    user_id: uuid.UUID | None = Query(default=None),
) -> list[AnalyticsEventRead]:
    # Only moderators can view analytics
    if current_user.role not in (
        UserRole.MODERATOR,
        UserRole.ADMIN,
        UserRole.SUPER_ADMIN,
    ):
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
@router.post(
    "/events", response_model=AnalyticsEventRead, status_code=status.HTTP_201_CREATED
)
async def create_analytics_event(
    payload: AnalyticsEventCreate,
    current_user: User = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
) -> AnalyticsEventRead:
    event = AnalyticsEvent(
        user_id=current_user.id if current_user else None,
        property_id=payload.property_id,
        event_type=payload.event_type,
        payload=payload.payload,
        ip_address=payload.ip_address,
        user_agent=payload.user_agent,
    )
    db.add(event)
    await db.commit()
    await db.refresh(event)
    return event


@router.get("/popular-searches", response_model=list[PopularSearchRead])
async def popular_searches(
    db: AsyncSession = Depends(get_db),
    limit: int = Query(default=10, ge=1, le=50),
    days: int = Query(default=7, ge=1, le=90),
) -> list[PopularSearchRead]:
    """Most frequent search queries over the last N days (public)."""
    from datetime import UTC, datetime, timedelta

    since = datetime.now(UTC) - timedelta(days=days)
    query_expr = AnalyticsEvent.payload["query"].as_string()
    stmt = (
        select(query_expr.label("query"), func.count(AnalyticsEvent.id).label("count"))
        .where(
            AnalyticsEvent.event_type == "search",
            AnalyticsEvent.created_at >= since,
        )
        .group_by(query_expr)
        .order_by(func.count(AnalyticsEvent.id).desc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    return [
        PopularSearchRead(query=query, count=count)
        for query, count in result.all()
        if query
    ]
