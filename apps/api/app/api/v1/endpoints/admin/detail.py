from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import Field
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies.auth import get_current_user
from app.db.session import get_db
from app.models.agency import Agency, Agent
from app.models.enums import UserRole
from app.models.moderation import ModerationLog
from app.models.property import (
    Property,
    PropertyLocation,
)
from app.models.report import Report
from app.models.user import User
from app.schemas.agency import AgencyRead
from app.schemas.agent import AgentRead
from app.schemas.auth import UserRead
from app.schemas.property import (
    PropertyRead,
)
from app.schemas.report import ReportRead

router = APIRouter(tags=["admin-moderation-detail"])


# Dependency to check for admin/moderator/super_admin access
def get_admin_user(
    current_user: User = Depends(get_current_user),
) -> User:
    if current_user.role not in (
        UserRole.MODERATOR,
        UserRole.ADMIN,
        UserRole.SUPER_ADMIN,
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )
    return current_user


# Schema for admin property detail response
class AdminPropertyDetailRead(PropertyRead):
    """Extended property detail for admin/moderator view."""

    # Seller information
    seller: UserRead

    # Agency information (if applicable)
    agency: AgencyRead | None = None
    agent: AgentRead | None = None

    # Reports
    reports: list[ReportRead] = Field(default_factory=list)

    # Moderation timeline/history
    moderation_timeline: list[dict] = Field(default_factory=list)

    # Analytics counters
    analytics: dict[str, Any] = Field(default_factory=dict)

    # Duplicate detection signals
    duplicate_signals: list[dict] = Field(default_factory=list)


@router.get("/admin/listings/{property_id}")
async def get_admin_property_detail(
    property_id: uuid.UUID,
    admin_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
) -> AdminPropertyDetailRead:
    """Get detailed property information for admin/moderator review."""

    # Get the property with relationships
    from app.repositories.property import PropertyRepository

    repo = PropertyRepository(db)
    prop = await repo.get_by_id(property_id)
    if not prop:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Property not found",
        )

    # Get the base property data
    base_property = repo.to_read(prop)

    # Get seller information
    seller = None
    if prop.owner:
        seller_result = await db.execute(select(User).where(User.id == prop.owner.id))
        seller_user = seller_result.scalar_one_or_none()
        if seller_user:
            seller = UserRead.model_validate(seller_user)

    # Get agency information
    agency = None
    if prop.agency:
        agency_result = await db.execute(
            select(Agency).where(Agency.id == prop.agency.id)
        )
        agency_obj = agency_result.scalar_one_or_none()
        if agency_obj:
            agency = AgencyRead.model_validate(agency_obj)

    # Get agent information
    agent = None
    if prop.agent:
        agent_result = await db.execute(select(Agent).where(Agent.id == prop.agent.id))
        agent_obj = agent_result.scalar_one_or_none()
        if agent_obj:
            agent = AgentRead.model_validate(agent_obj)

    # Get reports for this property
    reports_result = await db.execute(
        select(Report)
        .where(Report.property_id == prop.id)
        .order_by(Report.created_at.desc())
    )
    reports = reports_result.scalars().all()
    reports_read = [ReportRead.model_validate(report) for report in reports]

    # Get moderation timeline/history
    moderation_result = await db.execute(
        select(ModerationLog, User.full_name)
        .join(User, ModerationLog.moderator_id == User.id)
        .where(ModerationLog.property_id == prop.id)
        .order_by(ModerationLog.created_at.desc())
    )
    moderation_entries = moderation_result.all()
    moderation_timeline = []
    for log, moderator_name in moderation_entries:
        moderation_timeline.append(
            {
                "id": str(log.id),
                "who": moderator_name or "Unknown",
                "what": log.action.value
                if hasattr(log.action, "value")
                else str(log.action),
                "reason": log.reason or "",
                "timestamp": log.created_at.isoformat() if log.created_at else None,
            }
        )

    # Get analytics counters for this property
    # Views count is already in the property
    # Get additional analytics if needed
    analytics = {
        "views": prop.views or 0,
        # Could add more analytics here like favorites count, etc.
    }

    # Duplicate detection signals: search for other listings that look like
    # the same offer (same city/district, same deal/property type, similar
    # rooms, price and area, and similar title).
    duplicate_signals: list[dict] = []
    find_dupes = select(Property)
    loc_clauses = []
    if prop.location:
        if prop.location.city:
            loc_clauses.append(PropertyLocation.city == prop.location.city)
        if prop.location.district:
            loc_clauses.append(PropertyLocation.district == prop.location.district)
    if loc_clauses:
        find_dupes = find_dupes.join(
            PropertyLocation, PropertyLocation.property_id == Property.id
        ).where(and_(*loc_clauses))
    find_dupes = find_dupes.where(
        Property.id != prop.id,
        Property.deal_type == prop.deal_type,
        Property.status.in_(["active", "pending_review", "suspended"]),
    )
    if prop.rooms:
        min_rooms = max(prop.rooms - 1, 0)
        find_dupes = find_dupes.where(Property.rooms.between(min_rooms, prop.rooms + 1))
    similar = (await db.execute(find_dupes.limit(50))).scalars().all()

    target_price = float(prop.price) if prop.price is not None else None
    target_area = float(prop.area_total) if prop.area_total is not None else None

    def _norm_title(title: str) -> str:
        return "".join(ch.lower() for ch in str(title) if ch.isalnum())

    target_title = _norm_title(prop.title)
    for candidate in similar:
        signals = []
        candidate_price = (
            float(candidate.price) if candidate.price is not None else None
        )
        candidate_area = (
            float(candidate.area_total) if candidate.area_total is not None else None
        )
        if candidate.owner_id == prop.owner_id:
            signals.append("same_owner")
        if (
            target_price
            and candidate_price
            and abs(candidate_price - target_price) <= max(target_price * 0.05, 100)
        ):
            signals.append("price_within_5pct")
        if (
            target_area
            and candidate_area
            and abs(candidate_area - target_area) <= max(target_area * 0.1, 2)
        ):
            signals.append("area_within_10pct")
        if target_title and _norm_title(candidate.title) == target_title:
            signals.append("identical_title")
        elif target_title and (
            target_title in _norm_title(candidate.title)
            or _norm_title(candidate.title) in target_title
        ):
            signals.append("similar_title")
        if not signals:
            continue
        # Confidence: weighted overlap of the signals
        weights = {
            "same_owner": 0.35,
            "price_within_5pct": 0.2,
            "area_within_10pct": 0.15,
            "similar_title": 0.15,
            "identical_title": 0.3,
        }
        confidence = round(min(sum(weights[s] for s in signals), 1.0) * 100, 1)
        only_if = confidence >= 40
        duplicate_signals.append(
            {
                "id": str(candidate.id),
                "reference_code": candidate.reference_code,
                "title": candidate.title,
                "price": candidate_price,
                "area_total": candidate_area,
                "rooms": candidate.rooms,
                "status": candidate.status.value
                if hasattr(candidate.status, "value")
                else str(candidate.status),
                "owner_id": str(candidate.owner_id),
                "same_owner": "same_owner" in signals,
                "signals": signals,
                "confidence": confidence,
                "flag_for_review": only_if,
            }
        )
    duplicate_signals.sort(key=lambda s: -s["confidence"])

    # Construct the response by extending the base property data
    # Exclude the seller field from base property as we're providing a more detailed one
    base_property_data = base_property.model_dump(exclude={"seller"})
    response_data = AdminPropertyDetailRead(
        **base_property_data,
        seller=seller,
        agency=agency,
        agent=agent,
        reports=reports_read,
        moderation_timeline=moderation_timeline,
        analytics=analytics,
        duplicate_signals=duplicate_signals,
    )

    return response_data


# Create the main admin router for detail views
admin_detail_router = APIRouter()
admin_detail_router.include_router(router, prefix="")
