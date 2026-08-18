"""Admin advertising CRUD + stats (Phase 15)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies.auth import get_current_user
from app.db.session import get_db
from app.models.ad_campaign import AdCampaign
from app.models.ad_daily_stats import AdDailyStats
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.ad_campaign import (
    PLACEMENT_DIMS,
    AdCampaignCreate,
    AdCampaignRead,
    AdCampaignUpdate,
)
from app.services.admin_log import log_admin_action

router = APIRouter(prefix="/admin/advertising", tags=["admin-advertising"])

ADMIN_ROLES = (UserRole.ADMIN, UserRole.SUPER_ADMIN)


def _require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role not in ADMIN_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user


def _validate_url(url: str) -> bool:
    """Reject unsafe URL schemes."""
    if not url:
        return False
    blocked = ("javascript:", "data:", "file:", "vbscript:", "about:")
    url_lower = url.lower().strip()
    for scheme in blocked:
        if url_lower.startswith(scheme):
            return False
    return url_lower.startswith(("http://", "https://"))


@router.get("", response_model=list[AdCampaignRead])
async def admin_list_campaigns(
    current_user: User = Depends(_require_admin),
    db: AsyncSession = Depends(get_db),
    state: str | None = Query(
        default=None, pattern="^(DRAFT|SCHEDULED|ACTIVE|PAUSED|EXPIRED|ARCHIVED)$"
    ),
    placement: str | None = Query(default=None),
    search: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[AdCampaignRead]:
    stmt = select(AdCampaign).order_by(desc(AdCampaign.created_at))
    if placement:
        stmt = stmt.where(AdCampaign.placement == placement)
    if search:
        stmt = stmt.where(
            or_(
                AdCampaign.name.ilike(f"%{search}%"),
                AdCampaign.advertiser.ilike(f"%{search}%"),
            )
        )
    result = await db.execute(stmt.offset(offset).limit(limit))
    campaigns = list(result.scalars().all())
    if state:
        campaigns = [c for c in campaigns if c.state == state]
    return campaigns


@router.post("", response_model=AdCampaignRead, status_code=status.HTTP_201_CREATED)
async def admin_create_campaign(
    payload: AdCampaignCreate,
    current_user: User = Depends(_require_admin),
    db: AsyncSession = Depends(get_db),
) -> AdCampaignRead:
    if not _validate_url(payload.destination_url):
        raise HTTPException(400, "Destination URL must use http:// or https:// scheme")
    if payload.start_at and payload.end_at and payload.start_at >= payload.end_at:
        raise HTTPException(400, "start_at must be before end_at")

    campaign = AdCampaign(
        **payload.model_dump(),
        created_by=current_user.id,
    )
    db.add(campaign)
    await db.flush()
    await log_admin_action(
        db,
        admin_id=current_user.id,
        action="ad_campaign.create",
        entity_type="ad_campaign",
        entity_id=campaign.id,
        details={"name": campaign.name, "placement": campaign.placement},
    )
    await db.commit()
    await db.refresh(campaign)
    return campaign


@router.get("/placements", response_model=dict[str, dict])
async def admin_get_placements(
    current_user: User = Depends(_require_admin),
) -> dict:
    """Return all placements with recommended dimensions for admin UI."""
    return {
        placement: {
            "recommended_width": dims[0],
            "recommended_height": dims[1],
            "aspect_ratio": round(dims[0] / dims[1], 2) if dims[1] else None,
        }
        for placement, dims in PLACEMENT_DIMS.items()
    }


@router.get("/{campaign_id}", response_model=AdCampaignRead)
async def admin_get_campaign(
    campaign_id: uuid.UUID,
    current_user: User = Depends(_require_admin),
    db: AsyncSession = Depends(get_db),
) -> AdCampaignRead:
    campaign = await db.get(AdCampaign, campaign_id)
    if not campaign:
        raise HTTPException(404, "Campaign not found")
    return campaign


@router.patch("/{campaign_id}", response_model=AdCampaignRead)
async def admin_update_campaign(
    campaign_id: uuid.UUID,
    payload: AdCampaignUpdate,
    current_user: User = Depends(_require_admin),
    db: AsyncSession = Depends(get_db),
) -> AdCampaignRead:
    campaign = await db.get(AdCampaign, campaign_id)
    if not campaign:
        raise HTTPException(404, "Campaign not found")

    update_data = payload.model_dump(exclude_unset=True)

    if "destination_url" in update_data and not _validate_url(
        update_data["destination_url"]
    ):
        raise HTTPException(400, "Destination URL must use http:// or https:// scheme")
    if "start_at" in update_data and "end_at" in update_data:
        if (
            update_data["start_at"]
            and update_data["end_at"]
            and update_data["start_at"] >= update_data["end_at"]
        ):
            raise HTTPException(400, "start_at must be before end_at")
    elif "start_at" in update_data and update_data["start_at"] and campaign.end_at:
        if update_data["start_at"] >= campaign.end_at:
            raise HTTPException(400, "start_at must be before end_at")
    elif (
        "end_at" in update_data
        and update_data["end_at"]
        and campaign.start_at >= update_data["end_at"]
    ):
        raise HTTPException(400, "start_at must be before end_at")

    for key, value in update_data.items():
        setattr(campaign, key, value)

    await db.flush()
    await log_admin_action(
        db,
        admin_id=current_user.id,
        action="ad_campaign.update",
        entity_type="ad_campaign",
        entity_id=campaign.id,
        details=update_data,
    )
    await db.commit()
    await db.refresh(campaign)
    return campaign


@router.post("/{campaign_id}/pause", response_model=AdCampaignRead)
async def admin_pause_campaign(
    campaign_id: uuid.UUID,
    current_user: User = Depends(_require_admin),
    db: AsyncSession = Depends(get_db),
) -> AdCampaignRead:
    campaign = await db.get(AdCampaign, campaign_id)
    if not campaign:
        raise HTTPException(404, "Campaign not found")
    campaign.enabled = False
    await db.flush()
    await log_admin_action(
        db,
        admin_id=current_user.id,
        action="ad_campaign.pause",
        entity_type="ad_campaign",
        entity_id=campaign.id,
    )
    await db.commit()
    await db.refresh(campaign)
    return campaign


@router.post("/{campaign_id}/resume", response_model=AdCampaignRead)
async def admin_resume_campaign(
    campaign_id: uuid.UUID,
    current_user: User = Depends(_require_admin),
    db: AsyncSession = Depends(get_db),
) -> AdCampaignRead:
    campaign = await db.get(AdCampaign, campaign_id)
    if not campaign:
        raise HTTPException(404, "Campaign not found")
    campaign.enabled = True
    await db.flush()
    await log_admin_action(
        db,
        admin_id=current_user.id,
        action="ad_campaign.resume",
        entity_type="ad_campaign",
        entity_id=campaign.id,
    )
    await db.commit()
    await db.refresh(campaign)
    return campaign


@router.post("/{campaign_id}/archive", response_model=AdCampaignRead)
async def admin_archive_campaign(
    campaign_id: uuid.UUID,
    current_user: User = Depends(_require_admin),
    db: AsyncSession = Depends(get_db),
) -> AdCampaignRead:
    campaign = await db.get(AdCampaign, campaign_id)
    if not campaign:
        raise HTTPException(404, "Campaign not found")
    campaign.archived = True
    campaign.enabled = False
    await db.flush()
    await log_admin_action(
        db,
        admin_id=current_user.id,
        action="ad_campaign.archive",
        entity_type="ad_campaign",
        entity_id=campaign.id,
    )
    await db.commit()
    await db.refresh(campaign)
    return campaign


@router.delete("/{campaign_id}", status_code=status.HTTP_200_OK)
async def admin_delete_campaign(
    campaign_id: uuid.UUID,
    current_user: User = Depends(_require_admin),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    campaign = await db.get(AdCampaign, campaign_id)
    if not campaign:
        raise HTTPException(404, "Campaign not found")
    await db.delete(campaign)
    await db.flush()
    await log_admin_action(
        db,
        admin_id=current_user.id,
        action="ad_campaign.delete",
        entity_type="ad_campaign",
        entity_id=campaign_id,
    )
    await db.commit()
    return {"message": "Campaign deleted"}


# ----- Stats endpoints -----


@router.get("/overview/stats", response_model=dict)
async def admin_advertising_overview(
    current_user: User = Depends(_require_admin),
    db: AsyncSession = Depends(get_db),
    days: int = Query(default=30, ge=1, le=365),
) -> dict:
    since = datetime.now(UTC) - timedelta(days=days)

    # Totals
    total_impr = await db.scalar(select(func.sum(AdCampaign.impressions))) or 0
    total_clicks = await db.scalar(select(func.sum(AdCampaign.clicks))) or 0
    total_ctr = total_clicks / total_impr if total_impr else 0.0

    # Top campaign
    top_campaign = await db.execute(
        select(AdCampaign).order_by(desc(AdCampaign.impressions)).limit(1)
    )
    top_campaign = top_campaign.scalar_one_or_none()

    # Top placement
    placement_stats = await db.execute(
        select(
            AdCampaign.placement,
            func.sum(AdCampaign.impressions).label("imps"),
            func.sum(AdCampaign.clicks).label("clks"),
        )
        .group_by(AdCampaign.placement)
        .order_by(desc("imps"))
    )
    top_placement = placement_stats.first()

    # Daily trend
    daily_trend = await db.execute(
        select(
            AdDailyStats.date,
            func.sum(AdDailyStats.impressions).label("imps"),
            func.sum(AdDailyStats.clicks).label("clks"),
        )
        .where(AdDailyStats.date >= since)
        .group_by(AdDailyStats.date)
        .order_by(AdDailyStats.date)
    )
    trend = [
        {
            "date": row.date.isoformat(),
            "impressions": row.imps or 0,
            "clicks": row.clks or 0,
            "ctr": (row.clks / row.imps) if row.imps else 0.0,
        }
        for row in daily_trend.all()
    ]

    return {
        "period_days": days,
        "total_impressions": total_impr,
        "total_clicks": total_clicks,
        "ctr": total_ctr,
        "top_campaign": {
            "id": str(top_campaign.id),
            "name": top_campaign.name,
            "impressions": top_campaign.impressions,
            "clicks": top_campaign.clicks,
            "ctr": top_campaign.ctr,
        }
        if top_campaign
        else None,
        "top_placement": {
            "placement": top_placement.placement,
            "impressions": top_placement.imps or 0,
            "clicks": top_placement.clks or 0,
        }
        if top_placement
        else None,
        "daily_trend": trend,
    }


@router.get("/{campaign_id}/stats", response_model=dict)
async def admin_campaign_stats(
    campaign_id: uuid.UUID,
    current_user: User = Depends(_require_admin),
    db: AsyncSession = Depends(get_db),
    days: int = Query(default=30, ge=1, le=365),
) -> dict:
    campaign = await db.get(AdCampaign, campaign_id)
    if not campaign:
        raise HTTPException(404, "Campaign not found")

    since = datetime.now(UTC) - timedelta(days=days)
    stmt = (
        select(AdDailyStats)
        .where(
            AdDailyStats.campaign_id == campaign_id,
            AdDailyStats.date >= since,
        )
        .order_by(AdDailyStats.date)
    )
    daily = list((await db.execute(stmt)).scalars().all())

    total_impressions = sum(d.impressions for d in daily)
    total_clicks = sum(d.clicks for d in daily)
    ctr = total_clicks / total_impressions if total_impressions else 0.0

    trend = [
        {
            "date": d.date.isoformat(),
            "impressions": d.impressions,
            "clicks": d.clicks,
            "ctr": d.ctr,
        }
        for d in daily
    ]

    return {
        "campaign_id": str(campaign_id),
        "period_days": days,
        "total_impressions": total_impressions,
        "total_clicks": total_clicks,
        "ctr": ctr,
        "trend": trend,
    }
