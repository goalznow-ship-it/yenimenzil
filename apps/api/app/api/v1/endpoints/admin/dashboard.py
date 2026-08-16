from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies.auth import get_current_user
from app.db.session import get_db
from app.models.agency import Agency, Agent
from app.models.enums import ReportStatus, UserRole
from app.models.property import Property
from app.models.report import Report
from app.models.user import User

router = APIRouter(tags=["admin-dashboard"])


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


@router.get("/admin/dashboard/stats")
async def get_admin_dashboard_stats(
    admin_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Get admin dashboard overview statistics."""

    # Total users
    total_users_stmt = select(func.count(User.id))
    total_users_result = await db.execute(total_users_stmt)
    total_users = total_users_result.scalar() or 0

    # Active users (is_active = True)
    active_users_stmt = select(func.count(User.id)).where(User.is_active == True)
    active_users_result = await db.execute(active_users_stmt)
    active_users = active_users_result.scalar() or 0

    # Total listings
    total_listings_stmt = select(func.count(Property.id))
    total_listings_result = await db.execute(total_listings_stmt)
    total_listings = total_listings_result.scalar() or 0

    # Active listings (status = active)
    active_listings_stmt = select(func.count(Property.id)).where(
        Property.status == "active"
    )
    active_listings_result = await db.execute(active_listings_stmt)
    active_listings = active_listings_result.scalar() or 0

    # Pending review (status = pending_review)
    pending_review_stmt = select(func.count(Property.id)).where(
        Property.status == "pending_review"
    )
    pending_review_result = await db.execute(pending_review_stmt)
    pending_review = pending_review_result.scalar() or 0

    # Rejected listings (status = rejected)
    rejected_listings_stmt = select(func.count(Property.id)).where(
        Property.status == "rejected"
    )
    rejected_listings_result = await db.execute(rejected_listings_stmt)
    rejected_listings = rejected_listings_result.scalar() or 0

    # Sold (status = sold)
    sold_listings_stmt = select(func.count(Property.id)).where(
        Property.status == "sold"
    )
    sold_listings_result = await db.execute(sold_listings_stmt)
    sold_listings = sold_listings_result.scalar() or 0

    # Rented (status = rented)
    rented_listings_stmt = select(func.count(Property.id)).where(
        Property.status == "rented"
    )
    rented_listings_result = await db.execute(rented_listings_stmt)
    rented_listings = rented_listings_result.scalar() or 0

    # Total agencies
    total_agencies_stmt = select(func.count(Agency.id))
    total_agencies_result = await db.execute(total_agencies_stmt)
    total_agencies = total_agencies_result.scalar() or 0

    # Total agents
    total_agents_stmt = select(func.count(Agent.id))
    total_agents_result = await db.execute(total_agents_stmt)
    total_agents = total_agents_result.scalar() or 0

    # Reports open (status = open)
    reports_open_stmt = select(func.count(Report.id)).where(
        Report.status == ReportStatus.OPEN.value
    )
    reports_open_result = await db.execute(reports_open_stmt)
    reports_open = reports_open_result.scalar() or 0

    # Listings created today
    today_start = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
    listings_today_stmt = select(func.count(Property.id)).where(
        Property.created_at >= today_start
    )
    listings_today_result = await db.execute(listings_today_stmt)
    listings_today = listings_today_result.scalar() or 0

    # Listings created this week
    week_start = today_start - timedelta(days=today_start.weekday())
    listings_week_stmt = select(func.count(Property.id)).where(
        Property.created_at >= week_start
    )
    listings_week_result = await db.execute(listings_week_stmt)
    listings_week = listings_week_result.scalar() or 0

    return {
        "total_users": total_users,
        "active_users": active_users,
        "total_listings": total_listings,
        "active_listings": active_listings,
        "pending_review": pending_review,
        "rejected_listings": rejected_listings,
        "sold": sold_listings,
        "rented": rented_listings,
        "total_agencies": total_agencies,
        "total_agents": total_agents,
        "reports_open": reports_open,
        "listings_created_today": listings_today,
        "listings_created_this_week": listings_week,
    }


@router.get("/admin/dashboard/charts/listings-over-time")
async def get_listings_over_time_chart(
    admin_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
    days: int = Query(default=30, ge=1, le=365),
) -> list[dict[str, Any]]:
    """Get listings created over time for charting."""

    start_date = datetime.now(UTC) - timedelta(days=days)

    # Group by date and count listings created
    stmt = (
        select(
            func.date(Property.created_at).label("date"),
            func.count(Property.id).label("count"),
        )
        .where(Property.created_at >= start_date)
        .group_by(func.date(Property.created_at))
        .order_by(func.date(Property.created_at))
    )

    result = await db.execute(stmt)
    rows = result.all()

    # Format for charting library
    chart_data = [
        {"date": row.date.isoformat() if row.date else None, "count": row.count}
        for row in rows
    ]

    return chart_data


@router.get("/admin/dashboard/charts/users-over-time")
async def get_users_over_time_chart(
    admin_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
    days: int = Query(default=30, ge=1, le=365),
) -> list[dict[str, Any]]:
    """Get users registered over time for charting."""

    start_date = datetime.now(UTC) - timedelta(days=days)

    # Group by date and count users created
    stmt = (
        select(
            func.date(User.created_at).label("date"), func.count(User.id).label("count")
        )
        .where(User.created_at >= start_date)
        .group_by(func.date(User.created_at))
        .order_by(func.date(User.created_at))
    )

    result = await db.execute(stmt)
    rows = result.all()

    # Format for charting library
    chart_data = [
        {"date": row.date.isoformat() if row.date else None, "count": row.count}
        for row in rows
    ]

    return chart_data


@router.get("/admin/dashboard/charts/deal-type-distribution")
async def get_deal_type_distribution_chart(
    admin_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    """Get deal type distribution for charting."""

    # Count listings by deal type
    stmt = (
        select(
            Property.deal_type.label("deal_type"),
            func.count(Property.id).label("count"),
        )
        .group_by(Property.deal_type)
        .order_by(func.count(Property.id).desc())
    )

    result = await db.execute(stmt)
    rows = result.all()

    # Format for charting library
    chart_data = [{"deal_type": row.deal_type, "count": row.count} for row in rows]

    return chart_data


@router.get("/admin/dashboard/charts/property-type-distribution")
async def get_property_type_distribution_chart(
    admin_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    """Get property type distribution for charting."""

    # Count listings by property type
    stmt = (
        select(
            Property.property_type.label("property_type"),
            func.count(Property.id).label("count"),
        )
        .group_by(Property.property_type)
        .order_by(func.count(Property.id).desc())
    )

    result = await db.execute(stmt)
    rows = result.all()

    # Format for charting library
    chart_data = [
        {"property_type": row.property_type, "count": row.count} for row in rows
    ]

    return chart_data


# Create the main admin router
admin_router = APIRouter()
admin_router.include_router(router)
# Import and include other admin routers here to avoid circular imports
from .agency import admin_agencies_router
from .analytics import admin_analytics_router
from .audit import admin_audit_router
from .detail import admin_detail_router
from .features import admin_features_router
from .intelligence import admin_intelligence_router
from .listings import admin_listings_router
from .locations import admin_locations_router
from .platform import admin_platform_router
from .promotions import admin_promotions_router
from .report import admin_reports_router
from .users import admin_users_router
from .wallet import admin_wallet_router

admin_router.include_router(admin_listings_router)
admin_router.include_router(admin_detail_router)
admin_router.include_router(admin_users_router)
admin_router.include_router(admin_agencies_router)
admin_router.include_router(admin_reports_router)
admin_router.include_router(admin_audit_router)
admin_router.include_router(admin_promotions_router)
admin_router.include_router(admin_features_router)
admin_router.include_router(admin_locations_router)
admin_router.include_router(admin_intelligence_router)
admin_router.include_router(admin_analytics_router)
admin_router.include_router(admin_wallet_router)
from .advertising import router as admin_advertising_router

admin_router.include_router(admin_advertising_router)
admin_router.include_router(admin_platform_router)
