from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies.auth import get_current_user
from app.db.session import get_db
from app.models.enums import ReportStatus, UserRole
from app.models.report import Report
from app.models.user import User
from app.schemas.report import ReportRead

router = APIRouter(tags=["admin-reports"])


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


# Dependency for destructive report operations (admin/super_admin only)
def get_senior_admin_user(
    current_user: User = Depends(get_admin_user),
) -> User:
    if current_user.role not in (UserRole.ADMIN, UserRole.SUPER_ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    return current_user


class AdminReportUpdate(BaseModel):
    description: str | None = Field(None, max_length=2000)
    status: ReportStatus | None = None
    resolution_note: str | None = Field(None, max_length=2000)


@router.get("/admin/reports")
async def admin_list_reports(
    admin_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
    # Pagination
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    # Search
    search: str | None = Query(default=None),
    # Filters
    status: ReportStatus | None = Query(default=None),
    # Date range
    created_after: datetime | None = Query(default=None),
    created_before: datetime | None = Query(default=None),
    # Sorting
    sort_by: str = Query(default="created_at", pattern="^(created_at|reason)$"),
    sort_order: str = Query(default="desc", pattern="^(asc|desc)$"),
) -> dict[str, Any]:
    """Admin endpoint to list reports with filtering, search, and pagination."""
    
    # Base query
    query = select(Report)
    
    # Apply search
    if search:
        search_term = f"%{search}%"
        query = query.where(
            or_(
                Report.description.ilike(search_term),
            )
        )
    
    # Apply filters
    if status:
        query = query.where(Report.status == status)
    if created_after:
        query = query.where(Report.created_at >= created_after)
    if created_before:
        query = query.where(Report.created_at <= created_before)
    
    # Apply sorting
    if sort_order == "asc":
        query = query.order_by(getattr(Report, sort_by).asc())
    else:
        query = query.order_by(getattr(Report, sort_by).desc())
    
    # Get total count for pagination
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    # Apply pagination
    offset = (page - 1) * limit
    query = query.offset(offset).limit(limit)
    
    # Execute query
    result = await db.execute(query)
    reports = result.scalars().all()
    
    # Format response
    report_list = []
    for report in reports:
        report_list.append({
            "id": str(report.id),
            "property_id": str(report.property_id),
            "reporter_id": str(report.reporter_id) if report.reporter_id else None,
            "reviewer_id": str(report.reviewer_id) if report.reviewer_id else None,
            "reason": report.reason,  # Already the string value of the enum
            "description": report.description,
            "status": report.status,  # Already the string value of the enum
            "resolution_note": report.resolution_note,
            "created_at": report.created_at.isoformat() if report.created_at else None,
            "reviewed_at": report.reviewed_at.isoformat() if report.reviewed_at else None,
        })
    
    return {
        "data": report_list,
        "pagination": {
            "page": page,
            "limit": limit,
            "total": total,
            "pages": (total + limit - 1) // limit,
        },
        "filters": {
            "status": [s.value for s in ReportStatus],
        }
    }


@router.get("/admin/reports/{report_id}", response_model=ReportRead)
async def admin_get_report(
    report_id: uuid.UUID,
    admin_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
) -> ReportRead:
    """Get a specific report's details."""
    report = await db.get(Report, report_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found",
        )
    return ReportRead.model_validate(report)


@router.patch("/admin/reports/{report_id}", response_model=ReportRead)
async def admin_update_report(
    report_id: uuid.UUID,
    report_update: AdminReportUpdate,
    admin_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
) -> ReportRead:
    """Update a report's status/resolution and record the reviewer."""
    report = await db.get(Report, report_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found",
        )
    
    # Update report fields if provided
    update_data = report_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(report, field):
            setattr(report, field, value)
    
    # Record the reviewer
    report.reviewer_id = admin_user.id
    if report.status == ReportStatus.RESOLVED and report.reviewed_at is None:
        report.reviewed_at = datetime.now(UTC)
    
    await db.commit()
    await db.refresh(report)
    return ReportRead.model_validate(report)


@router.delete("/admin/reports/{report_id}")
async def admin_delete_report(
    report_id: uuid.UUID,
    admin_user: User = Depends(get_senior_admin_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Delete a report (admin/super_admin only)."""
    report = await db.get(Report, report_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found",
        )
    
    await db.delete(report)
    await db.commit()
    
    return {
        "message": "Report deleted successfully",
        "report_id": str(report_id),
    }


# Create the main admin router for reports
admin_reports_router = APIRouter()
admin_reports_router.include_router(router, prefix="")