"""Admin audit logging helper."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.admin_log import AdminActionLog


async def log_admin_action(
    db: AsyncSession,
    *,
    admin_id: uuid.UUID | None,
    action: str,
    entity_type: str,
    entity_id: uuid.UUID | None = None,
    details: dict[str, Any] | None = None,
    ip_address: str | None = None,
) -> None:
    """Record an admin operation in the audit log (fire-and-forget insert)."""
    db.add(
        AdminActionLog(
            admin_id=admin_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            details=details or {},
            ip_address=ip_address,
        )
    )
