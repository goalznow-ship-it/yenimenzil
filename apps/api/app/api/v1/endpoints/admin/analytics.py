from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies.auth import get_current_user
from app.db.session import get_db
from app.models.analytics import AnalyticsEvent
from app.models.enums import AnalyticsEventType, UserRole
from app.models.favorite import Favorite
from app.models.property import Property, PropertyLocation
from app.models.user import User

router = APIRouter(tags=["admin-analytics"])


def get_admin_user(
    current_user: User = Depends(get_current_user),
) -> User:
    if current_user.role not in (UserRole.MODERATOR, UserRole.ADMIN, UserRole.SUPER_ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )
    return current_user


@router.get("/admin/analytics/marketplace")
async def admin_marketplace_analytics(
    admin_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
    days: int = Query(default=30, ge=1, le=365),
) -> dict[str, Any]:
    """Marketplace engagement analytics over the last N days."""
    from datetime import UTC, datetime, timedelta

    since = datetime.now(UTC) - timedelta(days=days)

    event_rows = await db.execute(
        select(AnalyticsEvent.event_type, func.count(AnalyticsEvent.id))
        .where(AnalyticsEvent.created_at >= since)
        .group_by(AnalyticsEvent.event_type)
    )
    events = {evt: count for evt, count in event_rows.all()}

    total_views = events.get(AnalyticsEventType.PROPERTY_VIEW.value, 0)
    total_favorites = events.get(AnalyticsEventType.PROPERTY_FAVORITE.value, 0) - events.get(
        AnalyticsEventType.PROPERTY_UNFAVORITE.value, 0
    )
    total_unfavorites = events.get(AnalyticsEventType.PROPERTY_UNFAVORITE.value, 0)
    phone_reveals = events.get(AnalyticsEventType.PHONE_REVEAL.value, 0)
    whatsapp_clicks = events.get(AnalyticsEventType.WHATSAPP_CLICK.value, 0)
    searches = events.get(AnalyticsEventType.SEARCH.value, 0)

    favorites_stored = (
        await db.execute(select(func.count(Favorite.id)))
    ).scalar() or 0

    # Per-property-type overview
    prop_type_rows = await db.execute(
        select(Property.property_type, func.count(Property.id))
        .group_by(Property.property_type)
    )
    listings_by_type = {
        (t.value if hasattr(t, "value") else str(t)): count
        for t, count in prop_type_rows.all()
    }

    # Location breakdown (cities by listings)
    city_rows = await db.execute(
        select(PropertyLocation.city, func.count(Property.id))
        .join(Property, Property.id == PropertyLocation.property_id)
        .where(PropertyLocation.city.is_not(None))
        .group_by(PropertyLocation.city)
        .order_by(func.count(Property.id).desc())
        .limit(15)
    )
    listings_by_city = [
        {"city": city, "listings": count} for city, count in city_rows.all()
    ]

    # Top viewed listings
    top_rows = await db.execute(
        select(Property.id, Property.title, Property.reference_code, Property.views)
        .order_by(Property.views.desc())
        .limit(10)
    )
    top_listings = [
        {
            "id": str(row.id),
            "title": row.title,
            "reference_code": row.reference_code,
            "views": row.views,
        }
        for row in top_rows.all()
    ]

    return {
        "period_days": days,
        "views": total_views,
        "favorites": max(total_favorites, 0),
        "unfavorites": total_unfavorites,
        "favorites_stored": favorites_stored,
        "phone_reveals": phone_reveals,
        "whatsapp_clicks": whatsapp_clicks,
        "searches": searches,
        "engagement_rate": (
            round(total_views / favorites_stored, 2) if favorites_stored else None
        ),
        "listings_by_type": listings_by_type,
        "listings_by_city": listings_by_city,
        "top_listings": top_listings,
    }


admin_analytics_router = APIRouter()
admin_analytics_router.include_router(router, prefix="")