from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies.auth import get_current_user
from app.db.session import get_db
from app.models.enums import UserRole
from app.models.moderation import ModerationLog
from app.models.user import User
from app.schemas.moderation import ModerationLogCreate, ModerationLogRead

router = APIRouter(prefix="/moderation", tags=["moderation"])


@router.get("/logs", response_model=list[ModerationLogRead])
async def list_moderation_logs(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    property_id: uuid.UUID | None = Query(default=None),
    moderator_id: uuid.UUID | None = Query(default=None),
    action: str | None = Query(default=None),
) -> list[ModerationLogRead]:
    # Only moderators can view logs
    if current_user.role not in (UserRole.MODERATOR, UserRole.ADMIN, UserRole.SUPER_ADMIN):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    stmt = select(ModerationLog).order_by(ModerationLog.created_at.desc())
    if property_id:
        stmt = stmt.where(ModerationLog.property_id == property_id)
    if moderator_id:
        stmt = stmt.where(ModerationLog.moderator_id == moderator_id)
    if action:
        stmt = stmt.where(ModerationLog.action == action)
    stmt = stmt.offset(offset).limit(limit)
    result = await db.execute(stmt)
    logs = result.scalars().all()
    return list(logs)


@router.post("/logs", response_model=ModerationLogRead, status_code=status.HTTP_201_CREATED)
async def create_moderation_log(
    payload: ModerationLogCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ModerationLogRead:
    # Only moderators can create logs
    if current_user.role not in (UserRole.MODERATOR, UserRole.ADMIN, UserRole.SUPER_ADMIN):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    log = ModerationLog(
        property_id=payload.property_id,
        moderator_id=payload.moderator_id,
        action=payload.action,
        reason=payload.reason,
    )
    db.add(log)
    await db.commit()
    await db.refresh(log)
    return log
