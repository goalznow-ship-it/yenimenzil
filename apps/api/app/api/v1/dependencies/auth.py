"""Auth dependencies: current user, role guards, CSRF origin check."""

from __future__ import annotations

import uuid

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.security import ACCESS_TOKEN_COOKIE, decode_access_token
from app.db.session import get_db
from app.models.enums import UserRole
from app.models.user import User

settings = get_settings()


def _extract_access_token(request: Request) -> str | None:
    token = request.cookies.get(ACCESS_TOKEN_COOKIE)
    if not token:
        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
    return token


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> User:
    token = _extract_access_token(request)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    payload = decode_access_token(token)
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )
    user = await db.get(User, uuid.UUID(user_id))
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found"
        )
    return user


async def get_optional_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> User | None:
    token = _extract_access_token(request)
    if not token:
        return None
    try:
        payload = decode_access_token(token)
        user_id = payload.get("sub")
        if not user_id:
            return None
        user = await db.get(User, uuid.UUID(user_id))
        return user if user is not None and user.is_active else None
    except HTTPException:
        return None


def require_roles(*roles: UserRole):
    async def dependency(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return user

    return dependency


STAFF_ROLES = (
    UserRole.MODERATOR,
    UserRole.ADMIN,
    UserRole.SUPER_ADMIN,
)


def verify_origin(request: Request) -> None:
    """CSRF guard: mutating cookie-authenticated requests must come from
    a same-site origin. Cross-site fetches can't set a custom Origin."""
    if request.method in {"GET", "HEAD", "OPTIONS"}:
        return
    origin = request.headers.get("origin")
    if not origin:
        return
    if origin not in settings.cors_origins_list:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid origin",
        )


def can_edit_property(prop, user: User) -> bool:
    """Whether a user may modify a property record (edit/delete/submit)."""
    if user.role in STAFF_ROLES:
        return True
    if prop.owner_id == user.id:
        return True
    if user.role == UserRole.AGENT and prop.agent_id is not None:
        for agent in user.agent_records or []:
            if agent.id == prop.agent_id:
                return True
    if user.role == UserRole.AGENCY_ADMIN and prop.agency_id is not None:
        for agent in user.agent_records or []:
            if agent.agency_id == prop.agency_id:
                return True
    return False
