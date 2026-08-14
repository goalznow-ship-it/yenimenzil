from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies.auth import get_current_user
from app.db.session import get_db
from app.models.enums import DealType, PropertyStatus, PropertyType, UserRole
from app.models.moderation import ModerationAction, ModerationLog
from app.models.property import Property
from app.models.report import Report
from app.models.user import User

router = APIRouter(tags=["admin-listings"])


# Dependency to check for admin/moderator/super_admin access
def get_admin_user(
    current_user: User = Depends(get_current_user),
) -> User:
    if current_user.role not in (
        UserRole.MODERATOR,
        UserRole.ADMIN,
        UserRole.SUPER_ADMIN,
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )
    return current_user


@router.get("/admin/listings")
async def admin_list_properties(
    admin_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
    # Pagination
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    # Search
    search: str | None = Query(default=None),
    # Filters
    status: PropertyStatus | None = Query(default=None),
    deal_type: DealType | None = Query(default=None),
    property_type: PropertyType | None = Query(default=None),
    city: str | None = Query(default=None),
    district: str | None = Query(default=None),
    owner_id: uuid.UUID | None = Query(default=None),
    agent_id: uuid.UUID | None = Query(default=None),
    agency_id: uuid.UUID | None = Query(default=None),
    verified: bool | None = Query(default=None),
    promoted: bool | None = Query(default=None),
    # Date range
    created_after: datetime | None = Query(default=None),
    created_before: datetime | None = Query(default=None),
    # Price range
    min_price: float | None = Query(default=None, ge=0),
    max_price: float | None = Query(default=None, ge=0),
    # Sorting
    sort_by: str = Query(
        default="created_at", pattern="^(created_at|title|price|status|views)$"
    ),
    sort_order: str = Query(default="desc", pattern="^(asc|desc)$"),
) -> dict[str, Any]:
    """Admin endpoint to list properties with filtering, search, and pagination."""

    # Base query
    query = select(Property).join(User, Property.owner_id == User.id, isouter=True)

    # Apply search
    if search:
        search_term = f"%{search}%"
        query = query.where(
            or_(
                Property.title.ilike(search_term),
                Property.description.ilike(search_term),
                User.full_name.ilike(search_term),
            )
        )

    # Apply filters
    if status:
        query = query.where(Property.status == status.value)
    if deal_type:
        query = query.where(Property.deal_type == deal_type.value)
    if property_type:
        query = query.where(Property.property_type == property_type.value)
    if city:
        query = query.where(Property.city.ilike(f"%{city}%"))
    if district:
        query = query.where(Property.district.ilike(f"%{district}%"))
    if owner_id:
        query = query.where(Property.owner_id == owner_id)
    if agent_id:
        query = query.where(Property.agent_id == agent_id)
    if agency_id:
        query = query.where(Property.agency_id == agency_id)
    if verified is not None:
        query = query.where(User.is_verified == verified)
    # Note: promoted filtering would require a promotion relationship/table
    if created_after:
        query = query.where(Property.created_at >= created_after)
    if created_before:
        query = query.where(Property.created_at <= created_before)
    if min_price is not None:
        query = query.where(Property.price >= min_price)
    if max_price is not None:
        query = query.where(Property.price <= max_price)

    # Apply sorting
    if sort_order == "asc":
        query = query.order_by(getattr(Property, sort_by).asc())
    else:
        query = query.order_by(getattr(Property, sort_by).desc())

    # Get total count for pagination
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Apply pagination
    offset = (page - 1) * limit
    query = query.offset(offset).limit(limit)

    # Execute query
    result = await db.execute(query)
    properties = result.scalars().all()

    # Format response
    property_list = []
    for prop in properties:
        # Get owner info
        owner_name = "N/A"
        owner_email = "N/A"
        if prop.owner:
            owner_name = prop.owner.full_name
            owner_email = prop.owner.email

        # Get agency info
        agency_name = "N/A"
        if prop.agency:
            agency_name = prop.agency.name

        # Count reports for this property
        reports_count_stmt = select(func.count(Report.id)).where(
            Report.property_id == prop.id
        )
        reports_count_result = await db.execute(reports_count_stmt)
        reports_count = reports_count_result.scalar() or 0

        property_list.append(
            {
                "id": str(prop.id),
                "reference_code": getattr(
                    prop, "reference_code", "N/A"
                ),  # Assuming this field exists
                "cover_image": prop.media[0].url if prop.media else None,
                "title": prop.title,
                "owner": {
                    "id": str(prop.owner.id) if prop.owner else None,
                    "name": owner_name,
                    "email": owner_email,
                },
                "agency": {
                    "id": str(prop.agency.id) if prop.agency else None,
                    "name": agency_name,
                }
                if prop.agency
                else None,
                "price": float(prop.price) if prop.price else 0,
                "price_currency": getattr(prop, "currency", "AZN"),
                "location": f"{prop.city}, {prop.district}"
                if prop.city and prop.district
                else "N/A",
                "status": prop.status,
                "created_at": prop.created_at.isoformat() if prop.created_at else None,
                "views": prop.views or 0,
                "reports_count": reports_count,
            }
        )

    return {
        "data": property_list,
        "pagination": {
            "page": page,
            "limit": limit,
            "total": total,
            "pages": (total + limit - 1) // limit,
        },
        "filters": {
            "status": [s.value for s in PropertyStatus],
            "deal_type": [d.value for d in DealType],
            "property_type": [pt.value for pt in PropertyType],
        },
    }


@router.post("/admin/listings/{property_id}/approve")
async def approve_listing(
    property_id: uuid.UUID,
    admin_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
    reason: str = Query(default="Approved by admin"),
) -> dict[str, Any]:
    """Approve a listing (change status to active)."""

    # Get the property
    prop = await db.get(Property, property_id)
    if not prop:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Property not found",
        )

    # Check if property can be approved (should be in pending_review or rejected)
    if prop.status not in [
        PropertyStatus.PENDING_REVIEW.value,
        PropertyStatus.REJECTED.value,
    ]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Property cannot be approved from status: {prop.status}",
        )

    # Update property status
    old_status = prop.status
    prop.status = PropertyStatus.ACTIVE.value
    prop.published_at = prop.published_at or datetime.now(UTC)

    # Create moderation log
    moderation_log = ModerationLog(
        property_id=prop.id,
        moderator_id=admin_user.id,
        action=ModerationAction.APPROVED.value,
        reason=reason,
    )
    db.add(moderation_log)

    await db.commit()
    await db.refresh(prop)

    return {
        "message": "Listing approved successfully",
        "property_id": str(prop.id),
        "old_status": old_status,
        "new_status": prop.status,
    }


@router.post("/admin/listings/{property_id}/reject")
async def reject_listing(
    property_id: uuid.UUID,
    admin_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
    reason: str = Query(..., min_length=1, description="Reason for rejection"),
) -> dict[str, Any]:
    """Reject a listing (change status to rejected)."""

    # Get the property
    prop = await db.get(Property, property_id)
    if not prop:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Property not found",
        )

    # Check if property can be rejected (should be in pending_review or active)
    if prop.status not in [
        PropertyStatus.PENDING_REVIEW.value,
        PropertyStatus.ACTIVE.value,
    ]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Property cannot be rejected from status: {prop.status}",
        )

    # Update property status
    old_status = prop.status
    prop.status = PropertyStatus.REJECTED.value

    # Create moderation log
    moderation_log = ModerationLog(
        property_id=prop.id,
        moderator_id=admin_user.id,
        action=ModerationAction.REJECTED.value,
        reason=reason,
    )
    db.add(moderation_log)

    await db.commit()
    await db.refresh(prop)

    return {
        "message": "Listing rejected successfully",
        "property_id": str(prop.id),
        "old_status": old_status,
        "new_status": prop.status,
    }


@router.post("/admin/listings/{property_id}/request-edit")
async def request_edit_listing(
    property_id: uuid.UUID,
    admin_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
    reason: str = Query(..., min_length=1, description="Reason for requesting edits"),
) -> dict[str, Any]:
    """Request edits for a listing (change status to pending_review)."""

    # Get the property
    prop = await db.get(Property, property_id)
    if not prop:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Property not found",
        )

    # Check if property can be sent for edits (should be in active, pending_review, or rejected)
    if prop.status not in [
        PropertyStatus.ACTIVE.value,
        PropertyStatus.PENDING_REVIEW.value,
        PropertyStatus.REJECTED.value,
    ]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Property cannot be sent for edits from status: {prop.status}",
        )

    # Update property status
    old_status = prop.status
    prop.status = PropertyStatus.PENDING_REVIEW.value

    # Create moderation log
    moderation_log = ModerationLog(
        property_id=prop.id,
        moderator_id=admin_user.id,
        action=ModerationAction.CHANGES_REQUESTED.value,
        reason=reason,
    )
    db.add(moderation_log)

    await db.commit()
    await db.refresh(prop)

    return {
        "message": "Edit request sent successfully",
        "property_id": str(prop.id),
        "old_status": old_status,
        "new_status": prop.status,
    }


@router.post("/admin/listings/{property_id}/suspend")
async def suspend_listing(
    property_id: uuid.UUID,
    admin_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
    reason: str = Query(..., min_length=1, description="Reason for suspension"),
) -> dict[str, Any]:
    """Suspend a listing."""

    # Get the property
    prop = await db.get(Property, property_id)
    if not prop:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Property not found",
        )

    # Check if property can be suspended (should be in active status)
    if prop.status != PropertyStatus.ACTIVE.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Property cannot be suspended from status: {prop.status}",
        )

    # Update property status
    old_status = prop.status
    prop.status = PropertyStatus.SUSPENDED.value

    # Create moderation log
    moderation_log = ModerationLog(
        property_id=prop.id,
        moderator_id=admin_user.id,
        action=ModerationAction.SUSPENDED.value,
        reason=reason,
    )
    db.add(moderation_log)

    await db.commit()
    await db.refresh(prop)

    return {
        "message": "Listing suspended successfully",
        "property_id": str(prop.id),
        "old_status": old_status,
        "new_status": prop.status,
    }


@router.post("/admin/listings/{property_id}/archive")
async def archive_listing(
    property_id: uuid.UUID,
    admin_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
    reason: str = Query(..., min_length=1, description="Reason for archiving"),
) -> dict[str, Any]:
    """Archive a listing."""

    # Get the property
    prop = await db.get(Property, property_id)
    if not prop:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Property not found",
        )

    # Check if property can be archived (should not already be archived)
    if prop.status == PropertyStatus.ARCHIVED.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Property is already archived",
        )

    # Update property status
    old_status = prop.status
    prop.status = PropertyStatus.ARCHIVED.value

    # Create moderation log
    moderation_log = ModerationLog(
        property_id=prop.id,
        moderator_id=admin_user.id,
        action=ModerationAction.ARCHIVED.value,
        reason=reason,
    )
    db.add(moderation_log)

    await db.commit()
    await db.refresh(prop)

    return {
        "message": "Listing archived successfully",
        "property_id": str(prop.id),
        "old_status": old_status,
        "new_status": prop.status,
    }


@router.post("/admin/listings/{property_id}/mark-sold")
async def mark_listing_sold(
    property_id: uuid.UUID,
    admin_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
    reason: str = Query(default="Marked as sold by admin"),
) -> dict[str, Any]:
    """Mark a listing as sold."""

    # Get the property
    prop = await db.get(Property, property_id)
    if not prop:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Property not found",
        )

    # Check if property can be marked as sold (should be in active status)
    if prop.status != PropertyStatus.ACTIVE.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Property cannot be marked as sold from status: {prop.status}",
        )

    # Update property status
    old_status = prop.status
    prop.status = PropertyStatus.SOLD.value

    # Create moderation log
    moderation_log = ModerationLog(
        property_id=prop.id,
        moderator_id=admin_user.id,
        action=ModerationAction.APPROVED.value,  # Using APPROVED as sold is a positive outcome
        reason=reason,
    )
    db.add(moderation_log)

    await db.commit()
    await db.refresh(prop)

    return {
        "message": "Listing marked as sold successfully",
        "property_id": str(prop.id),
        "old_status": old_status,
        "new_status": prop.status,
    }


@router.post("/admin/listings/{property_id}/mark-rented")
async def mark_listing_rented(
    property_id: uuid.UUID,
    admin_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
    reason: str = Query(default="Marked as rented by admin"),
) -> dict[str, Any]:
    """Mark a listing as rented."""

    # Get the property
    prop = await db.get(Property, property_id)
    if not prop:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Property not found",
        )

    # Check if property can be marked as rented (should be in active status)
    if prop.status != PropertyStatus.ACTIVE.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Property cannot be marked as rented from status: {prop.status}",
        )

    # Update property status
    old_status = prop.status
    prop.status = PropertyStatus.RENTED.value

    # Create moderation log
    moderation_log = ModerationLog(
        property_id=prop.id,
        moderator_id=admin_user.id,
        action=ModerationAction.APPROVED.value,  # Using APPROVED as rented is a positive outcome
        reason=reason,
    )
    db.add(moderation_log)

    await db.commit()
    await db.refresh(prop)

    return {
        "message": "Listing marked as rented successfully",
        "property_id": str(prop.id),
        "old_status": old_status,
        "new_status": prop.status,
    }


@router.delete("/admin/listings/{property_id}")
async def delete_listing(
    property_id: uuid.UUID,
    admin_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
    reason: str = Query(..., min_length=1, description="Reason for deletion"),
) -> dict[str, Any]:
    """Delete a listing permanently."""

    # Get the property
    prop = await db.get(Property, property_id)
    if not prop:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Property not found",
        )

    # Store property info for response before deletion
    prop_id = str(prop.id)
    prop_title = prop.title

    # Create moderation log before deletion
    moderation_log = ModerationLog(
        property_id=prop.id,
        moderator_id=admin_user.id,
        action="deleted",  # Custom action for deletion
        reason=reason,
    )
    db.add(moderation_log)

    # Delete the property (this will cascade delete related media, price history, etc.)
    await db.delete(prop)

    await db.commit()

    return {
        "message": "Listing deleted successfully",
        "property_id": prop_id,
        "title": prop_title,
    }


# Bulk actions
@router.post("/admin/listings/bulk-approve")
async def bulk_approve_listings(
    property_ids: list[uuid.UUID],
    admin_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
    reason: str = Query(default="Bulk approved by admin"),
) -> dict[str, Any]:
    """Approve multiple listings in bulk."""

    if not property_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No property IDs provided",
        )

    # Get all properties
    result = await db.execute(select(Property).where(Property.id.in_(property_ids)))
    properties = result.scalars().all()

    if not properties:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No properties found with provided IDs",
        )

    updated_count = 0
    for prop in properties:
        # Only approve properties that can be approved
        if prop.status in [
            PropertyStatus.PENDING_REVIEW.value,
            PropertyStatus.REJECTED.value,
        ]:
            prop.status = PropertyStatus.ACTIVE.value
            prop.published_at = prop.published_at or datetime.now(UTC)

            # Create moderation log
            moderation_log = ModerationLog(
                property_id=prop.id,
                moderator_id=admin_user.id,
                action=ModerationAction.APPROVED.value,
                reason=reason,
            )
            db.add(moderation_log)
            updated_count += 1

    await db.commit()

    return {
        "message": f"{updated_count} listings approved successfully",
        "updated_count": updated_count,
        "total_requested": len(property_ids),
    }


@router.post("/admin/listings/bulk-suspend")
async def bulk_suspend_listings(
    property_ids: list[uuid.UUID],
    admin_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
    reason: str = Query(default="Bulk suspended by admin"),
) -> dict[str, Any]:
    """Suspend multiple listings in bulk."""

    if not property_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No property IDs provided",
        )

    # Get all properties
    result = await db.execute(select(Property).where(Property.id.in_(property_ids)))
    properties = result.scalars().all()

    if not properties:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No properties found with provided IDs",
        )

    updated_count = 0
    for prop in properties:
        # Only suspend properties that are active
        if prop.status == PropertyStatus.ACTIVE.value:
            prop.status = PropertyStatus.SUSPENDED.value

            # Create moderation log
            moderation_log = ModerationLog(
                property_id=prop.id,
                moderator_id=admin_user.id,
                action=ModerationAction.SUSPENDED.value,
                reason=reason,
            )
            db.add(moderation_log)
            updated_count += 1

    await db.commit()

    return {
        "message": f"{updated_count} listings suspended successfully",
        "updated_count": updated_count,
        "total_requested": len(property_ids),
    }


@router.post("/admin/listings/bulk-archive")
async def bulk_archive_listings(
    property_ids: list[uuid.UUID],
    admin_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
    reason: str = Query(default="Bulk archived by admin"),
) -> dict[str, Any]:
    """Archive multiple listings in bulk."""

    if not property_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No property IDs provided",
        )

    # Get all properties
    result = await db.execute(select(Property).where(Property.id.in_(property_ids)))
    properties = result.scalars().all()

    if not properties:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No properties found with provided IDs",
        )

    updated_count = 0
    for prop in properties:
        # Only archive properties that are not already archived
        if prop.status != PropertyStatus.ARCHIVED.value:
            prop.status = PropertyStatus.ARCHIVED.value

            # Create moderation log
            moderation_log = ModerationLog(
                property_id=prop.id,
                moderator_id=admin_user.id,
                action=ModerationAction.ARCHIVED.value,
                reason=reason,
            )
            db.add(moderation_log)
            updated_count += 1

    await db.commit()

    return {
        "message": f"{updated_count} listings archived successfully",
        "updated_count": updated_count,
        "total_requested": len(property_ids),
    }


# Create the main admin router for listings
admin_listings_router = APIRouter()
admin_listings_router.include_router(router, prefix="")
