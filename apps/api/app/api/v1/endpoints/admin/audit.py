from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, literal_column, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies.auth import get_current_user
from app.db.session import get_db
from app.models.admin_log import AdminActionLog
from app.models.enums import UserRole
from app.models.moderation import ModerationLog
from app.models.user import User

router = APIRouter(tags=["admin-audit"])


def get_admin_user(
    current_user: User = Depends(get_current_user),
) -> User:
    if current_user.role not in (UserRole.MODERATOR, UserRole.ADMIN, UserRole.SUPER_ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )
    return current_user


@router.get("/admin/audit-logs")
async def admin_audit_logs(
    admin_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=50, ge=1, le=200),
    action: str | None = Query(default=None),
    entity_type: str | None = Query(default=None),
    created_after: datetime | None = Query(default=None),
    created_before: datetime | None = Query(default=None),
) -> dict[str, Any]:
    """Admin audit log feed combining admin action logs and moderation logs."""
    query = (
        select(AdminActionLog, User.full_name, AdminActionLog.created_at, literal_column("'admin_actions'"))
        .join(User, AdminActionLog.admin_id == User.id, isouter=True)
    )

    if action:
        query = query.where(AdminActionLog.action == action)
    if entity_type:
        query = query.where(AdminActionLog.entity_type == entity_type)
    if created_after:
        query = query.where(AdminActionLog.created_at >= created_after)
    if created_before:
        query = query.where(AdminActionLog.created_at <= created_before)

    # Moderation logs (from the moderation pipeline)
    mod_query = (
        select(ModerationLog, User.full_name, ModerationLog.created_at, literal_column("'moderation'"))
        .join(User, ModerationLog.moderator_id == User.id)
        .where(ModerationLog.property_id.is_not(None))
    )
    if action:
        mod_query = mod_query.where(ModerationLog.action == action)
    if created_after:
        mod_query = mod_query.where(ModerationLog.created_at >= created_after)
    if created_before:
        mod_query = mod_query.where(ModerationLog.created_at <= created_before)

    # Fetch one page worth of entries across both sources in descending order
    total_admin = (await db.execute(
        select(func.count()).select_from(query.subquery())
    )).scalar() or 0
    total_mod = (await db.execute(
        select(func.count()).select_from(mod_query.subquery())
    )).scalar() or 0
    total = total_admin + total_mod

    offset = (page - 1) * limit
    admin_rows = (await db.execute(query.order_by(AdminActionLog.created_at.desc()).offset(offset).limit(limit))).all()
    mod_rows = (await db.execute(mod_query.order_by(ModerationLog.created_at.desc()).offset(offset).limit(limit))).all()

    entries = [
        {
            "id": str(row[0].id),
            "actor": row[1],
            "action": row[0].action,
            "entity_type": row[0].entity_type,
            "entity_id": str(row[0].entity_id) if row[0].entity_id else None,
            "details": row[0].details,
            "created_at": row[2].isoformat() if row[2] else None,
            "source": row[3],
        }
        for row in admin_rows
    ]
    entries += [
        {
            "id": str(row[0].id),
            "actor": row[1],
            "action": "moderation." + (row[0].action.value if hasattr(row[0].action, "value") else str(row[0].action)),
            "entity_type": "property",
            "entity_id": str(row[0].property_id),
            "details": {"reason": row[0].reason},
            "created_at": row[2].isoformat() if row[2] else None,
            "source": row[3],
        }
        for row in mod_rows
    ]

    # Merge and re-sort by created_at (both sources already individually ordered;
    # merge only if both non-empty)
    def key(e):
        return e["created_at"] or ""

    entries.sort(key=key, reverse=True)
    entries = entries[:limit]

    return {
        "data": entries,
        "pagination": {
            "page": page,
            "limit": limit,
            "total": total,
            "pages": (total + limit - 1) // limit,
        },
        "filters": {
            "entity_types": ["user", "property", "report", "agency", "feature", "promotion", "agent"],
        },
    }


admin_audit_router = APIRouter()
admin_audit_router.include_router(router, prefix="")