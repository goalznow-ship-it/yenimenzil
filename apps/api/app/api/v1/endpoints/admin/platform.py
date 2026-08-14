"""Admin-managed platform configuration: feature flags, homepage banners,
and broadcast announcements."""

from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies.auth import get_current_user
from app.db.session import get_db
from app.models.enums import UserRole
from app.models.platform import AdminAnnouncement, FeatureFlag, HomepageBanner
from app.models.user import User
from app.services.admin_log import log_admin_action

router = APIRouter(tags=["admin-platform"])

admin_platform_router = router


def get_admin_user(
    current_user: User = Depends(get_current_user),
) -> User:
    if current_user.role not in (UserRole.ADMIN, UserRole.SUPER_ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )
    return current_user


# ---------------- Feature flags ----------------


class FeatureFlagCreate(BaseModel):
    key: str = Field(min_length=2, max_length=100, pattern=r"^[a-z0-9_.-]+$")
    enabled: bool = False
    description: str = Field(default="", max_length=300)


class FeatureFlagUpdate(BaseModel):
    enabled: bool | None = None
    description: str | None = Field(None, max_length=300)


class FeatureFlagRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    key: str
    enabled: bool
    description: str
    updated_at: datetime


class BannerRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title_az: str
    subtitle_az: str
    image_url: str | None
    link_url: str | None
    cta_label_az: str | None
    badge_az: str | None
    sort_order: int
    active: bool
    created_at: datetime
    updated_at: datetime


@router.get("/admin/platform/flags")
async def admin_list_flags(
    admin_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
) -> list[FeatureFlagRead]:
    result = await db.execute(select(FeatureFlag).order_by(FeatureFlag.key))
    return list(result.scalars().all())


@router.post(
    "/admin/platform/flags",
    response_model=FeatureFlagRead,
    status_code=status.HTTP_201_CREATED,
)
async def admin_create_flag(
    payload: FeatureFlagCreate,
    admin_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
) -> FeatureFlagRead:
    existing = await db.execute(
        select(FeatureFlag).where(FeatureFlag.key == payload.key)
    )
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(status_code=400, detail="Flag key already exists")
    flag = FeatureFlag(**payload.model_dump())
    db.add(flag)
    await db.flush()
    await log_admin_action(
        db,
        admin_id=admin_user.id,
        action="flag.create",
        entity_type="feature_flag",
        entity_id=flag.id,
        details={"key": flag.key, "enabled": flag.enabled},
    )
    await db.commit()
    await db.refresh(flag)
    return flag


@router.patch("/admin/platform/flags/{flag_id}", response_model=FeatureFlagRead)
async def admin_update_flag(
    flag_id: uuid.UUID,
    payload: FeatureFlagUpdate,
    admin_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
) -> FeatureFlagRead:
    flag = await db.get(FeatureFlag, flag_id)
    if flag is None:
        raise HTTPException(status_code=404, detail="Flag not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(flag, key, value)
    await db.flush()
    await log_admin_action(
        db,
        admin_id=admin_user.id,
        action="flag.update",
        entity_type="feature_flag",
        entity_id=flag.id,
        details=payload.model_dump(exclude_unset=True),
    )
    await db.commit()
    await db.refresh(flag)
    return flag


@router.get("/public/platform/flags")
async def public_list_flags(db: AsyncSession = Depends(get_db)) -> dict[str, bool]:
    """Public feature flags for the frontend (enabled flags only)."""
    result = await db.execute(select(FeatureFlag).where(FeatureFlag.enabled.is_(True)))
    return {flag.key: True for flag in result.scalars().all()}


# ---------------- Homepage banners ----------------


class BannerCreate(BaseModel):
    title_az: str = Field(min_length=2, max_length=200)
    subtitle_az: str = Field(default="", max_length=300)
    image_url: str | None = Field(None, max_length=1000)
    link_url: str | None = Field(None, max_length=1000)
    cta_label_az: str | None = Field(None, max_length=100)
    badge_az: str | None = Field(None, max_length=100)
    sort_order: int = 0
    active: bool = True


class BannerUpdate(BaseModel):
    title_az: str | None = Field(None, min_length=2, max_length=200)
    subtitle_az: str | None = Field(None, max_length=300)
    image_url: str | None = Field(None, max_length=1000)
    link_url: str | None = Field(None, max_length=1000)
    cta_label_az: str | None = Field(None, max_length=100)
    badge_az: str | None = Field(None, max_length=100)
    sort_order: int | None = None
    active: bool | None = None


@router.get("/admin/platform/banners")
async def admin_list_banners(
    admin_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
) -> list[BannerRead]:
    result = await db.execute(
        select(HomepageBanner).order_by(
            HomepageBanner.sort_order, HomepageBanner.created_at
        )
    )
    return list(result.scalars().all())


@router.post(
    "/admin/platform/banners",
    response_model=BannerRead,
    status_code=status.HTTP_201_CREATED,
)
async def admin_create_banner(
    payload: BannerCreate,
    admin_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
) -> HomepageBanner:
    banner = HomepageBanner(**payload.model_dump())
    db.add(banner)
    await db.flush()
    await log_admin_action(
        db,
        admin_id=admin_user.id,
        action="banner.create",
        entity_type="homepage_banner",
        entity_id=banner.id,
    )
    await db.commit()
    await db.refresh(banner)
    return banner


@router.patch("/admin/platform/banners/{banner_id}", response_model=BannerRead)
async def admin_update_banner(
    banner_id: uuid.UUID,
    payload: BannerUpdate,
    admin_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
) -> BannerRead:
    banner = await db.get(HomepageBanner, banner_id)
    if banner is None:
        raise HTTPException(status_code=404, detail="Banner not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(banner, key, value)
    await db.flush()
    await log_admin_action(
        db,
        admin_id=admin_user.id,
        action="banner.update",
        entity_type="homepage_banner",
        entity_id=banner.id,
    )
    await db.commit()
    await db.refresh(banner)
    return banner


@router.delete("/admin/platform/banners/{banner_id}")
async def admin_delete_banner(
    banner_id: uuid.UUID,
    admin_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    banner = await db.get(HomepageBanner, banner_id)
    if banner is None:
        raise HTTPException(status_code=404, detail="Banner not found")
    await db.delete(banner)
    await db.flush()
    await log_admin_action(
        db,
        admin_id=admin_user.id,
        action="banner.delete",
        entity_type="homepage_banner",
        entity_id=banner_id,
    )
    await db.commit()
    return {"message": "Banner deleted"}


@router.get("/public/platform/banners")
async def public_list_banners(
    db: AsyncSession = Depends(get_db),
) -> list[BannerRead]:
    result = await db.execute(
        select(HomepageBanner)
        .where(HomepageBanner.active.is_(True))
        .order_by(HomepageBanner.sort_order, HomepageBanner.created_at)
    )
    return list(result.scalars().all())


# ---------------- Broadcast announcements ----------------


class AnnouncementCreate(BaseModel):
    title: str = Field(min_length=2, max_length=200)
    message: str = Field(min_length=2)
    audience: str = Field(default="all", pattern="^(all|sellers|agents)$")
    link: str | None = Field(None, max_length=500)


@router.post(
    "/admin/platform/announcements",
    status_code=status.HTTP_201_CREATED,
)
async def admin_broadcast_announcement(
    payload: AnnouncementCreate,
    admin_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """Broadcast a notification to the target audience's inboxes."""
    from sqlalchemy import text

    announcement = AdminAnnouncement(
        admin_id=admin_user.id,
        title=payload.title,
        message=payload.message,
        audience=payload.audience,
        link=payload.link,
    )
    db.add(announcement)
    await db.flush()

    # Insert one Notification per matching user (bulk, no duplicates).
    role_filter = ""
    params: dict = {
        "title": payload.title,
        "message": payload.message,
        "link": payload.link,
    }
    if payload.audience == "agents":
        role_filter = "WHERE role IN ('agent', 'agency_admin')"
    elif payload.audience == "sellers":
        role_filter = "WHERE role IN ('owner', 'agent', 'agency_admin')"
    await db.execute(
        text(
            "INSERT INTO notifications (id, user_id, title, message, kind, link, is_read, created_at) "
            "SELECT gen_random_uuid(), id, :title, :message, 'announcement', :link, false, now() "
            "FROM users "
            f"{role_filter} "
            "ON CONFLICT DO NOTHING"
        ),
        params,
    )
    await log_admin_action(
        db,
        admin_id=admin_user.id,
        action="announcement.broadcast",
        entity_type="admin_announcement",
        entity_id=announcement.id,
        details={"audience": payload.audience},
    )
    await db.commit()
    return {"message": "Announcement broadcast", "audience": payload.audience}


admin_platform_router = router
