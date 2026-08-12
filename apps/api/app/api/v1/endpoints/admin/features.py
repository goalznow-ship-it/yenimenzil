from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies.auth import get_current_user
from app.db.session import get_db
from app.models.enums import PropertyType, UserRole
from app.models.property import PropertyFeature
from app.models.user import User
from app.services.admin_log import log_admin_action

router = APIRouter(tags=["admin-features"])


def get_admin_user(
    current_user: User = Depends(get_current_user),
) -> User:
    if current_user.role not in (UserRole.MODERATOR, UserRole.ADMIN, UserRole.SUPER_ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )
    return current_user


class FeatureCreate(BaseModel):
    code: str = Field(min_length=2, max_length=32, pattern=r"^[a-z0-9_]+$")
    label_az: str = Field(min_length=2, max_length=100)


class FeatureUpdate(BaseModel):
    label_az: str | None = Field(None, min_length=2, max_length=100)


@router.get("/admin/catalog/features")
async def admin_list_features(
    admin_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=100, ge=1, le=200),
    search: str | None = Query(default=None),
) -> dict[str, Any]:
    """List the feature catalog (codes shared with the frontend labels)."""
    query = select(PropertyFeature)
    if search:
        query = query.where(
            PropertyFeature.code.ilike(f"%{search}%") | PropertyFeature.label_az.ilike(f"%{search}%")
        )
    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar() or 0
    query = query.order_by(PropertyFeature.code).offset((page - 1) * limit).limit(limit)
    features = (await db.execute(query)).scalars().all()

    return {
        "data": [
            {
                "id": str(f.id),
                "code": f.code,
                "label_az": f.label_az,
                "created_at": f.created_at.isoformat() if f.created_at else None,
            }
            for f in features
        ],
        "pagination": {"page": page, "limit": limit, "total": total, "pages": (total + limit - 1) // limit},
        "property_types": [t.value for t in PropertyType],
    }


@router.post("/admin/catalog/features", status_code=status.HTTP_201_CREATED)
async def admin_create_feature(
    feature: FeatureCreate,
    admin_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Create a new feature catalog entry (unique code)."""
    existing = await db.execute(
        select(PropertyFeature).where(PropertyFeature.code == feature.code)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Feature code already exists",
        )
    new_feature = PropertyFeature(code=feature.code, label_az=feature.label_az)
    db.add(new_feature)
    await db.flush()
    await log_admin_action(
        db,
        admin_id=admin_user.id,
        action="feature.create",
        entity_type="feature",
        entity_id=new_feature.id,
        details={"code": feature.code, "label_az": feature.label_az},
    )
    await db.commit()
    return {"id": str(new_feature.id), "code": feature.code, "label_az": feature.label_az}


@router.patch("/admin/catalog/features/{feature_id}")
async def admin_update_feature(
    feature_id: uuid.UUID,
    feature_update: FeatureUpdate,
    admin_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Update a feature label."""
    feature = await db.get(PropertyFeature, feature_id)
    if not feature:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Feature not found",
        )
    update_data = feature_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(feature, field, value)
    await db.flush()
    await log_admin_action(
        db,
        admin_id=admin_user.id,
        action="feature.update",
        entity_type="feature",
        entity_id=feature_id,
        details=update_data,
    )
    await db.commit()
    return {"id": str(feature_id), "code": feature.code, "label_az": feature.label_az}


@router.delete("/admin/catalog/features/{feature_id}")
async def admin_delete_feature(
    feature_id: uuid.UUID,
    admin_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Delete a feature catalog entry."""
    feature = await db.get(PropertyFeature, feature_id)
    if not feature:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Feature not found",
        )
    await db.delete(feature)
    await db.flush()
    await log_admin_action(
        db,
        admin_id=admin_user.id,
        action="feature.delete",
        entity_type="feature",
        entity_id=feature_id,
    )
    await db.commit()
    return {"message": "Feature deleted", "feature_id": str(feature_id)}


admin_features_router = APIRouter()
admin_features_router.include_router(router, prefix="")