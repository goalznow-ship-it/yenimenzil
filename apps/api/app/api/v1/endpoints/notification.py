from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies.auth import get_current_user
from app.db.session import get_db
from app.models.notification import Notification
from app.models.user import User
from app.models.verification import NotificationPreference
from app.schemas.notification import (
    NotificationCreate,
    NotificationRead,
    NotificationUnreadCount,
    NotificationUpdate,
)
from app.schemas.verification import (
    NotificationPreferenceRead,
    NotificationPreferenceUpdate,
)

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=list[NotificationRead])
async def list_notifications(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    unread_only: bool = Query(default=False),
) -> list[NotificationRead]:
    stmt = select(Notification).where(Notification.user_id == current_user.id)
    if unread_only:
        stmt = stmt.where(Notification.is_read == False)
    stmt = stmt.offset(offset).limit(limit).order_by(Notification.created_at.desc())
    result = await db.execute(stmt)
    notifications = result.scalars().all()
    return list(notifications)


@router.post("", response_model=NotificationRead, status_code=status.HTTP_201_CREATED)
async def create_notification(
    payload: NotificationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> NotificationRead:
    # For now, only allow creating notifications for the current user? Or allow any user to create a notification for any user?
    # We'll restrict to only allow creating notifications for the current user for simplicity.
    if payload.user_id != current_user.id:
        raise HTTPException(
            status_code=403, detail="Can only create notifications for yourself"
        )
    notification = Notification(**payload.model_dump())
    db.add(notification)
    await db.commit()
    await db.refresh(notification)
    return notification


@router.patch("/{notification_id}", response_model=NotificationRead)
async def update_notification(
    notification_id: uuid.UUID,
    payload: NotificationUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> NotificationRead:
    result = await db.execute(
        select(Notification).where(
            Notification.id == notification_id, Notification.user_id == current_user.id
        )
    )
    notification = result.scalar_one_or_none()
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(notification, field, value)
    await db.commit()
    await db.refresh(notification)
    return notification


@router.delete(
    "/{notification_id}", status_code=status.HTTP_204_NO_CONTENT, response_model=None
)
async def delete_notification(
    notification_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    result = await db.execute(
        select(Notification).where(
            Notification.id == notification_id, Notification.user_id == current_user.id
        )
    )
    notification = result.scalar_one_or_none()
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    await db.delete(notification)
    await db.commit()


@router.post("/mark-all-read", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
async def mark_all_read(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    result = await db.execute(
        select(Notification).where(
            Notification.user_id == current_user.id,
            Notification.is_read == False,
        )
    )
    for notification in result.scalars().all():
        notification.is_read = True
    await db.commit()


@router.get("/unread-count", response_model=NotificationUnreadCount)
async def unread_count(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> NotificationUnreadCount:
    stmt = select(func.count(Notification.id)).where(
        Notification.user_id == current_user.id,
        Notification.is_read == False,
    )
    unread = await db.execute(stmt)
    return NotificationUnreadCount(unread=unread.scalar() or 0)


@router.get("/preferences", response_model=NotificationPreferenceRead)
async def get_preferences(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> NotificationPreferenceRead:
    prefs = await _get_preferences(db, current_user.id)
    return _prefs_read(prefs)


@router.put("/preferences", response_model=NotificationPreferenceRead)
async def update_preferences(
    payload: NotificationPreferenceUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> NotificationPreferenceRead:
    prefs = await _get_preferences(db, current_user.id)
    for pref in prefs:
        pref.email_enabled = payload.email_enabled
        pref.push_enabled = payload.push_enabled
    await db.commit()
    return _prefs_read(prefs)


async def _get_preferences(
    db: AsyncSession, user_id: uuid.UUID
) -> list[NotificationPreference]:
    result = await db.execute(
        select(NotificationPreference).where(NotificationPreference.user_id == user_id)
    )
    prefs = result.scalars().all()
    if not prefs:
        defaults = [
            ("general", True, True),
            ("message", True, True),
            ("viewing", True, True),
            ("listing", True, True),
            ("promotion", True, False),
            ("system", True, True),
        ]
        prefs = [
            NotificationPreference(
                user_id=user_id, kind=kind, email_enabled=em, push_enabled=ps
            )
            for kind, em, ps in defaults
        ]
        db.add_all(prefs)
        await db.flush()
    return list(prefs)


def _prefs_read(
    prefs: list[NotificationPreference],
) -> NotificationPreferenceRead:
    return NotificationPreferenceRead(
        email_enabled=all(p.email_enabled for p in prefs),
        push_enabled=all(p.push_enabled for p in prefs),
    )
