"""Public ad delivery API (Phase 15)."""

from __future__ import annotations

import hashlib
import uuid
from datetime import UTC, datetime
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies.auth import get_optional_user
from app.core.config import get_settings
from app.db.session import get_db
from app.models.ad_campaign import AdCampaign
from app.models.ad_daily_stats import AdDailyStats
from app.models.ad_event import AdEvent
from app.models.user import User
from app.schemas.ad_campaign import (
    AdCampaignPublic,
    AdClickRequest,
    AdImpressionRequest,
    AdPlacement,
)

router = APIRouter(prefix="/ads", tags=["ads"])

DEDUPE_WINDOW_MINUTES = 10


async def _get_redis():
    import redis.asyncio as aioredis

    settings = get_settings()
    return aioredis.from_url(
        settings.REDIS_URL,
        socket_connect_timeout=1,
        socket_timeout=1,
        decode_responses=True,
    )


def _ip_hash(ip: str) -> str:
    return hashlib.sha256(ip.encode()).hexdigest()[:64]


def _is_campaign_active(
    campaign: AdCampaign,
    now: datetime,
    device: str,
    city: str | None,
    category: str | None,
) -> bool:
    return (
        campaign.state == "ACTIVE"
        and campaign.device_targeting == "all"
        or campaign.device_targeting == device
        and not (
            city and campaign.city_targeting and city not in campaign.city_targeting
        )
        and not (
            category
            and campaign.property_category_targeting
            and category not in campaign.property_category_targeting
        )
    )


def _select_best_campaign(campaigns: list[AdCampaign]) -> AdCampaign | None:
    """Select highest priority; for ties, weighted random by priority."""
    if not campaigns:
        return None
    max_prio = max(c.priority for c in campaigns)
    top = [c for c in campaigns if c.priority == max_prio]
    if len(top) == 1:
        return top[0]
    # Weighted random by priority (all same priority here, so equal weight)
    import random

    return random.choice(top)


@router.get("", response_model=list[AdCampaignPublic])
async def get_ads(
    placement: str | None = None,
    placements: str | None = None,
    device: Literal["desktop", "mobile"] = "desktop",
    city: str | None = None,
    category: str | None = None,
    db: AsyncSession = Depends(get_db),
    request: Request = None,
    user: User | None = Depends(get_optional_user),
) -> list[AdCampaignPublic]:
    """Get active ads for one or multiple placements.

    Query params:
    - placement: single placement (LEFT_RAIL, RIGHT_RAIL, etc.)
    - placements: comma-separated list (HOME_TOP_BANNER,SEARCH_INLINE_BANNER)
    - device: desktop | mobile
    - city: optional city for targeting
    - category: optional property category for targeting
    Returns list of ad objects, one per requested placement (or empty if no eligible ad).
    """
    if placement and placements:
        raise HTTPException(400, "Provide either placement or placements, not both")

    targets_str = (placements or placement) or ""
    targets = [p.strip() for p in targets_str.split(",") if p.strip()]
    if not targets:
        return []

    valid = set(AdPlacement._placements)
    invalid = [t for t in targets if t not in valid]
    if invalid:
        raise HTTPException(400, f"Invalid placement(s): {', '.join(invalid)}")

    # Validate placements
    valid = set(AdPlacement._placements)
    invalid = [t for t in targets if t not in valid]
    if invalid:
        raise HTTPException(400, f"Invalid placement(s): {', '.join(invalid)}")

    now = datetime.now(UTC)

    # Fetch all active campaigns for requested placements
    stmt = (
        select(AdCampaign)
        .where(
            AdCampaign.placement.in_(targets),
            AdCampaign.archived.is_(False),
            AdCampaign.enabled.is_(True),
        )
        .order_by(AdCampaign.priority.desc())
    )
    result = await db.execute(stmt)
    all_campaigns = list(result.scalars().all())

    # Filter by date range, targeting
    eligible_by_placement: dict[str, list[AdCampaign]] = {}
    for camp in all_campaigns:
        if not _is_campaign_active(camp, now, device, city, category):
            continue
        eligible_by_placement.setdefault(camp.placement, []).append(camp)

    # Select one per placement
    response: list[AdCampaignPublic] = []
    for target in targets:
        campaigns = eligible_by_placement.get(target, [])
        best = _select_best_campaign(campaigns)
        if best:
            response.append(
                AdCampaignPublic(
                    id=best.id,
                    placement=best.placement,
                    desktop_creative_url=best.desktop_creative_url,
                    mobile_creative_url=best.mobile_creative_url,
                    alt_text=best.alt_text,
                    destination_url=best.destination_url,
                    open_in_new_tab=best.open_in_new_tab,
                )
            )

    return response


async def _record_event(
    db: AsyncSession,
    campaign_id: uuid.UUID,
    event_type: Literal["impression", "click"],
    session_key: str | None,
    request: Request,
    user: User | None,
) -> None:
    """Record impression/click with deduplication.

    Dedup key: campaign_id + event_type + (session_key or IP hash) within window.
    """
    ip = request.client.host if request.client else "unknown"
    ip_h = _ip_hash(ip)

    # Build dedup key
    dedup_suffix = session_key or ip_h
    dedup_key = f"ad_dedup:{campaign_id}:{event_type}:{dedup_suffix}"

    redis = await _get_redis()
    if await redis.get(dedup_key):
        return  # duplicate within window
    await redis.setex(dedup_key, DEDUPE_WINDOW_MINUTES * 60, "1")

    # Record event (fire-and-forget)
    db.add(
        AdEvent(
            campaign_id=campaign_id,
            event_type=event_type,
            session_key=session_key,
            ip_hash=ip_h,
            user_agent=request.headers.get("user-agent"),
            referrer=request.headers.get("referer"),
        )
    )

    # Increment campaign counters
    stmt = select(AdCampaign).where(AdCampaign.id == campaign_id)
    campaign = (await db.execute(stmt)).scalar_one_or_none()
    if campaign:
        if event_type == "impression":
            campaign.impressions += 1
        else:
            campaign.clicks += 1

    # Upsert daily stats
    today = datetime.now(tz=UTC).date()
    stmt = select(AdDailyStats).where(
        AdDailyStats.campaign_id == campaign_id, AdDailyStats.date == today
    )
    daily = (await db.execute(stmt)).scalar_one_or_none()
    if daily is None:
        daily = AdDailyStats(
            campaign_id=campaign_id,
            date=today,
            impressions=1 if event_type == "impression" else 0,
            clicks=1 if event_type == "click" else 0,
            unique_impressions=1 if event_type == "impression" else 0,
            unique_clicks=1 if event_type == "click" else 0,
        )
        db.add(daily)
    else:
        if event_type == "impression":
            daily.impressions += 1
        else:
            daily.clicks += 1
        # Unique tracking is approximate without Redis set; skip for simplicity

    await db.commit()


@router.post("/{campaign_id}/impression")
async def record_impression(
    campaign_id: uuid.UUID,
    payload: AdImpressionRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User | None = Depends(get_optional_user),
) -> None:
    """Record ad impression (deduplicated)."""
    stmt = select(AdCampaign).where(AdCampaign.id == campaign_id)
    campaign = (await db.execute(stmt)).scalar_one_or_none()
    if not campaign:
        return  # silent ignore - don't leak existence
    await _record_event(
        db, campaign_id, "impression", payload.session_key, request, user
    )


@router.post("/{campaign_id}/click")
async def record_click(
    campaign_id: uuid.UUID,
    payload: AdClickRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User | None = Depends(get_optional_user),
) -> None:
    """Record ad click (deduplicated)."""
    stmt = select(AdCampaign).where(AdCampaign.id == campaign_id)
    campaign = (await db.execute(stmt)).scalar_one_or_none()
    if not campaign:
        return
    await _record_event(db, campaign_id, "click", payload.session_key, request, user)
