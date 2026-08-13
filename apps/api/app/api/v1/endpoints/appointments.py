from __future__ import annotations

import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.api.v1.dependencies.auth import get_current_user
from app.db.session import get_db
from app.models.appointment import ViewingAppointment
from app.models.enums import PropertyStatus
from app.models.notification import Notification
from app.models.property import Property, PropertyMedia
from app.models.user import User
from app.schemas.appointment import (
    ViewingAppointmentCreate,
    ViewingAppointmentRead,
    ViewingAppointmentUpdate,
)

router = APIRouter(prefix="/viewing-requests", tags=["viewing-appointments"])


def _read(appointment: ViewingAppointment) -> ViewingAppointmentRead:
    return ViewingAppointmentRead(
        id=appointment.id,
        property_id=appointment.property_id,
        requester_id=appointment.requester_id,
        owner_id=appointment.owner_id,
        scheduled_at=appointment.scheduled_at,
        status=appointment.status,
        note=appointment.note,
        created_at=appointment.created_at,
        property_title=appointment.property.title if appointment.property else None,
        property_cover=(
            appointment.property.media[0].url
            if appointment.property and appointment.property.media
            else None
        ),
        requester_name=appointment.requester.full_name,
        owner_name=appointment.owner.full_name,
    )


async def _notify(
    db: AsyncSession,
    user_id: uuid.UUID,
    kind: str,
    title: str,
    message: str,
    link: str | None = None,
) -> None:
    db.add(
        Notification(
            user_id=user_id, kind=kind, title=title, message=message, link=link
        )
    )


@router.post("/{property_id}", response_model=ViewingAppointmentRead, status_code=201)
async def create_viewing_request(
    property_id: uuid.UUID,
    payload: ViewingAppointmentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ViewingAppointmentRead:
    property = await db.get(Property, property_id)
    if property is None:
        raise HTTPException(status_code=404, detail="Property not found")
    if property.status != PropertyStatus.ACTIVE.value:
        raise HTTPException(status_code=400, detail="Property is not active")
    if property.owner_id == current_user.id:
        raise HTTPException(
            status_code=400, detail="Cannot request a viewing of your own listing"
        )
    if payload.scheduled_at < datetime.now(UTC):
        raise HTTPException(status_code=400, detail="Scheduled time is in the past")

    appointment = ViewingAppointment(
        property_id=property.id,
        requester_id=current_user.id,
        owner_id=property.owner_id,
        scheduled_at=payload.scheduled_at,
        status="pending",
        note=payload.note,
    )
    db.add(appointment)
    await db.flush()
    await _notify(
        db,
        property.owner_id,
        "viewing",
        "Yeni baxış tələbi",
        f"{current_user.full_name} {property.title} elanına baxış tələb etdi.",
        f"/properties/{property.id}",
    )
    await db.commit()
    appointment = await _get_eager(db, appointment.id)
    return _read(appointment)


async def _get_eager(db: AsyncSession, appointment_id: uuid.UUID):
    result = await db.execute(
        select(ViewingAppointment)
        .where(ViewingAppointment.id == appointment_id)
        .options(
            joinedload(ViewingAppointment.property).joinedload(Property.media),
            joinedload(ViewingAppointment.requester),
            joinedload(ViewingAppointment.owner),
        )
    )
    return result.unique().scalar_one_or_none()


@router.get("", response_model=list[ViewingAppointmentRead])
async def list_my_appointments(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    role: str | None = Query(default=None, pattern=r"^(requested|hosted)$"),
    status_filter: str | None = Query(
        default=None,
        alias="status",
        pattern=r"^(pending|confirmed|declined|rescheduled|cancelled|completed)$",
    ),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[ViewingAppointmentRead]:
    me_id = current_user.id
    opts = (
        joinedload(ViewingAppointment.property).joinedload(Property.media),
        joinedload(ViewingAppointment.requester),
        joinedload(ViewingAppointment.owner),
    )
    if role == "requested":
        stmt = select(ViewingAppointment).where(
            ViewingAppointment.requester_id == me_id
        )
    elif role == "hosted":
        stmt = select(ViewingAppointment).where(ViewingAppointment.owner_id == me_id)
    else:
        stmt = select(ViewingAppointment).where(
            (ViewingAppointment.requester_id == me_id)
            | (ViewingAppointment.owner_id == me_id)
        )
    stmt = stmt.options(*opts)
    if status_filter:
        stmt = stmt.where(ViewingAppointment.status == status_filter)
    stmt = (
        stmt.order_by(ViewingAppointment.scheduled_at.desc())
        .offset(offset)
        .limit(limit)
    )
    result = await db.execute(stmt)
    appointments = result.unique().scalars().all()
    return [_read(a) for a in appointments]


@router.patch("/{appointment_id}", response_model=ViewingAppointmentRead)
async def update_appointment(
    appointment_id: uuid.UUID,
    payload: ViewingAppointmentUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ViewingAppointmentRead:
    appointment = await db.get(ViewingAppointment, appointment_id)
    if appointment is None:
        raise HTTPException(status_code=404, detail="Viewing request not found")

    is_owner = appointment.owner_id == current_user.id
    is_requester = appointment.requester_id == current_user.id
    if not is_owner and not is_requester:
        raise HTTPException(status_code=403, detail="Not your viewing request")

    if (
        payload.status
        and is_owner
        and payload.status
        not in (
            "confirmed",
            "declined",
            "cancelled",
            "completed",
        )
    ):
        raise HTTPException(
            status_code=400, detail="Invalid status transition for owner"
        )
    if (
        payload.status
        and is_requester
        and payload.status
        not in (
            "cancelled",
            "rescheduled",
        )
    ):
        raise HTTPException(
            status_code=400, detail="Invalid status transition for requester"
        )

    if payload.scheduled_at is not None:
        if payload.scheduled_at < datetime.now(UTC):
            raise HTTPException(status_code=400, detail="Scheduled time is in the past")
        if is_requester and appointment.status != "pending":
            raise HTTPException(
                status_code=400, detail="Reschedule is only possible while pending"
            )
        appointment.scheduled_at = payload.scheduled_at
        if appointment.status == "pending":
            appointment.status = "rescheduled"
    if payload.status:
        appointment.status = payload.status
    if payload.note is not None:
        appointment.note = payload.note

    await db.commit()
    appointment = await _get_eager(db, appointment.id)
    return _read(appointment)
