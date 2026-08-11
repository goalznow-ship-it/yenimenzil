from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies.auth import get_current_user
from app.db.session import get_db
from app.models.enums import ReportStatus, UserRole
from app.models.report import Report
from app.models.user import User
from app.schemas.report import ReportCreate, ReportRead, ReportUpdate

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("", response_model=list[ReportRead])
async def list_reports(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    property_id: uuid.UUID | None = Query(default=None),
    status: str | None = Query(default=None),
) -> list[ReportRead]:
    # Only moderators can list all reports
    if current_user.role not in (UserRole.MODERATOR, UserRole.ADMIN, UserRole.SUPER_ADMIN):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    stmt = select(Report).order_by(Report.created_at.desc())
    if property_id:
        stmt = stmt.where(Report.property_id == property_id)
    if status:
        stmt = stmt.where(Report.status == status)
    stmt = stmt.offset(offset).limit(limit)
    result = await db.execute(stmt)
    reports = result.scalars().all()
    return list(reports)


@router.post("", response_model=ReportRead, status_code=status.HTTP_201_CREATED)
async def create_report(
    payload: ReportCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ReportRead:
    reporter_id = current_user.id if payload.reporter_id is None else payload.reporter_id
    report = Report(
        property_id=payload.property_id,
        reporter_id=reporter_id,
        reason=payload.reason,
        description=payload.description,
        status=payload.status,
    )
    db.add(report)
    await db.commit()
    await db.refresh(report)
    return report


@router.patch("/{report_id}", response_model=ReportRead)
async def update_report(
    report_id: uuid.UUID,
    payload: ReportUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ReportRead:
    # Only moderators can update reports
    if current_user.role not in (UserRole.MODERATOR, UserRole.ADMIN, UserRole.SUPER_ADMIN):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    result = await db.execute(
        select(Report).where(Report.id == report_id)
    )
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    if payload.status is not None:
        report.status = payload.status
    if payload.resolution_note is not None:
        report.resolution_note = payload.resolution_note
    if payload.reviewer_id is not None:
        report.reviewer_id = payload.reviewer_id
    if payload.status in (ReportStatus.RESOLVED.value, ReportStatus.REJECTED.value):
        from datetime import UTC, datetime
        report.reviewed_at = datetime.now(UTC)
    await db.commit()
    await db.refresh(report)
    return report
