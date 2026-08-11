from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies.auth import get_current_user
from app.db.session import get_db
from app.models.favorite import Favorite
from app.models.notification import Notification
from app.models.property import Property
from app.models.user import User
from app.schemas.auth import UserRead, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserRead)
async def me(user: User = Depends(get_current_user)) -> UserRead:
    return UserRead.model_validate(user)


@router.patch("/me", response_model=UserRead)
async def update_me(
    payload: UserUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserRead:
    if payload.full_name is not None:
        user.full_name = payload.full_name.strip()
    if payload.phone is not None:
        user.phone = payload.phone
    if user.profile is not None:
        profile = user.profile
        if payload.bio is not None:
            profile.bio = payload.bio
        if payload.city is not None:
            profile.location = payload.city
        if payload.preferred_language is not None:
            profile.preferred_language = payload.preferred_language
    await db.commit()
    await db.refresh(user)
    return UserRead.model_validate(user)


@router.get("/me/dashboard")
async def get_user_dashboard(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return dashboard data for the current user."""
    # Number of properties by status
    stmt = (
        select(Property.status, func.count(Property.id))
        .where(Property.owner_id == current_user.id)
        .group_by(Property.status)
    )
    result = await db.execute(stmt)
    status_counts = {status: count for status, count in result.all()}

    # Total views across all properties
    stmt = select(func.sum(Property.views)).where(Property.owner_id == current_user.id)
    result = await db.execute(stmt)
    total_views = result.scalar() or 0

    # Total favorites count (how many users have favorited the user's properties)
    stmt = (
        select(func.count(Favorite.id))
        .join(Property, Favorite.property_id == Property.id)
        .where(Property.owner_id == current_user.id)
    )
    result = await db.execute(stmt)
    total_favorites = result.scalar() or 0

    # Unread notifications count
    stmt = (
        select(func.count(Notification.id))
        .where(
            Notification.user_id == current_user.id,
            Notification.is_read == False,
        )
    )
    result = await db.execute(stmt)
    unread_notifications = result.scalar() or 0

    return {
        "property_status_counts": status_counts,
        "total_views": int(total_views),
        "total_favorites": int(total_favorites),
        "unread_notifications": int(unread_notifications),
    }
