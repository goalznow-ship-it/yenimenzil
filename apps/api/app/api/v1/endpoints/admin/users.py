from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies.auth import get_current_user
from app.db.session import get_db
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.auth import UserRead
from app.services.admin_log import log_admin_action


# Schema for admin user update
class AdminUserUpdate(BaseModel):
    full_name: str | None = Field(None, min_length=2, max_length=150)
    phone: str | None = Field(None, pattern=r"^\+994\d{9}$")
    bio: str | None = Field(None, max_length=1000)
    city: str | None = Field(None, max_length=200)
    preferred_language: str | None = Field(None, pattern=r"^(az|ru|en)$")
    role: UserRole | None = None
    is_active: bool | None = None
    is_verified: bool | None = None

router = APIRouter(tags=["admin-users"])


# Dependency to check for admin/moderator/super_admin access
def get_admin_user(
    current_user: User = Depends(get_current_user),
) -> User:
    if current_user.role not in (UserRole.MODERATOR, UserRole.ADMIN, UserRole.SUPER_ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )
    return current_user


# Dependency for privilege-changing user operations (admin/super_admin only)
def get_senior_admin_user(
    current_user: User = Depends(get_admin_user),
) -> User:
    if current_user.role not in (UserRole.ADMIN, UserRole.SUPER_ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    return current_user


@router.get("/admin/users")
async def admin_list_users(
    admin_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
    # Pagination
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    # Search
    search: str | None = Query(default=None),
    # Filters
    role: UserRole | None = Query(default=None),
    is_active: bool | None = Query(default=None),
    is_verified: bool | None = Query(default=None),
    # Date range
    created_after: datetime | None = Query(default=None),
    created_before: datetime | None = Query(default=None),
    # Sorting
    sort_by: str = Query(default="created_at", pattern="^(created_at|email|full_name|role)$"),
    sort_order: str = Query(default="desc", pattern="^(asc|desc)$"),
) -> dict[str, Any]:
    """Admin endpoint to list users with filtering, search, and pagination."""
    
    # Base query
    query = select(User)
    
    # Apply search
    if search:
        search_term = f"%{search}%"
        query = query.where(
            or_(
                User.email.ilike(search_term),
                User.full_name.ilike(search_term),
            )
        )
    
    # Apply filters
    if role:
        query = query.where(User.role == role)
    if is_active is not None:
        query = query.where(User.is_active == is_active)
    if is_verified is not None:
        query = query.where(User.is_verified == is_verified)
    if created_after:
        query = query.where(User.created_at >= created_after)
    if created_before:
        query = query.where(User.created_at <= created_before)
    
    # Apply sorting
    if sort_order == "asc":
        query = query.order_by(getattr(User, sort_by).asc())
    else:
        query = query.order_by(getattr(User, sort_by).desc())
    
    # Get total count for pagination
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    # Apply pagination
    offset = (page - 1) * limit
    query = query.offset(offset).limit(limit)
    
    # Execute query
    result = await db.execute(query)
    users = result.scalars().all()
    
    # Format response
    user_list = []
    for user in users:
        # Get profile info if needed
        profile_info = None
        if user.profile:
            profile_info = {
                "avatar_url": user.profile.avatar_url,
                "bio": user.profile.bio,
                "location": user.profile.location,
                "preferred_language": user.profile.preferred_language,
                "member_since": user.profile.member_since.isoformat() if user.profile.member_since else None,
                "phone_verified": user.profile.phone_verified,
                "identity_verified": user.profile.identity_verified,
            }
        
        user_list.append({
            "id": str(user.id),
            "email": user.email,
            "phone": user.phone,
            "full_name": user.full_name,
            "role": user.role.value if isinstance(user.role, UserRole) else user.role,  # Return the string value of the enum
            "is_active": user.is_active,
            "is_verified": user.is_verified,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "updated_at": user.updated_at.isoformat() if user.updated_at else None,
            "profile": profile_info,
        })
    
    return {
        "data": user_list,
        "pagination": {
            "page": page,
            "limit": limit,
            "total": total,
            "pages": (total + limit - 1) // limit,
        },
        "filters": {
            "role": [r.value for r in UserRole],
        }
    }


@router.get("/admin/users/{user_id}")
async def admin_get_user(
    user_id: uuid.UUID,
    admin_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
) -> UserRead:
    """Get a specific user's details."""
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return UserRead.model_validate(user)


@router.patch("/admin/users/{user_id}")
async def admin_update_user(
    user_id: uuid.UUID,
    user_update: AdminUserUpdate,
    admin_user: User = Depends(get_senior_admin_user),
    db: AsyncSession = Depends(get_db),
) -> UserRead:
    """Update a user's details (role/is_active changes require admin or super_admin)."""
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    # Prevent deactivating or demoting yourself
    if user.id == admin_user.id and (
        user_update.is_active is False or (user_update.role and user_update.role != admin_user.role)
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot deactivate or demote your own account",
        )
    
    # Update user fields if provided
    update_data = user_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(user, field):
            setattr(user, field, value)

    await db.flush()
    await log_admin_action(
        db,
        admin_id=admin_user.id,
        action="user.update",
        entity_type="user",
        entity_id=user_id,
        details=update_data,
    )
    await db.commit()
    await db.refresh(user)
    return UserRead.model_validate(user)


@router.delete("/admin/users/{user_id}")
async def admin_delete_user(
    user_id: uuid.UUID,
    admin_user: User = Depends(get_senior_admin_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Deactivate a user (set is_active to False); admin/super_admin only."""
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    # Prevent self-deactivation
    if user.id == admin_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot deactivate your own account",
        )
    
    # Deactivate the user instead of deleting to preserve data integrity
    user.is_active = False
    await db.flush()
    await log_admin_action(
        db,
        admin_id=admin_user.id,
        action="user.deactivate",
        entity_type="user",
        entity_id=user_id,
    )
    await db.commit()
    
    return {
        "message": "User deactivated successfully",
        "user_id": str(user_id),
    }


# Create the main admin router for users
admin_users_router = APIRouter()
admin_users_router.include_router(router, prefix="")