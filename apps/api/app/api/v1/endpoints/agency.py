from __future__ import annotations

import csv
import io
import secrets
import uuid
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies.auth import get_current_user, get_optional_user
from app.db.session import get_db
from app.models.agency import Agency, Agent
from app.models.agency_invite import AgencyInvite
from app.models.enums import UserRole
from app.models.user import User
from app.repositories.property import PropertyRepository
from app.schemas.agency import AgencyCreate, AgencyRead, AgencyUpdate
from app.schemas.agency_invite import (
    AgencyImportResult,
    AgencyInviteCreate,
    AgencyInviteRead,
)
from app.schemas.agent import AgentRead
from app.schemas.analytics import AgencyAnalyticsRead
from app.schemas.property import PropertyCreate, PropertyQueryParams

router = APIRouter(prefix="/agencies", tags=["agencies"])

INVITE_TTL_DAYS = 7


def _require_admin_or_above(user: User) -> User:
    if user.role not in (UserRole.ADMIN, UserRole.SUPER_ADMIN):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    return user


async def _user_agent(db: AsyncSession, user: User) -> Agent | None:
    stmt = select(Agent).where(Agent.user_id == user.id)
    return (await db.execute(stmt)).scalar_one_or_none()


async def _require_agency_admin(db: AsyncSession, user: User) -> Agency:
    """User must be an agency_admin with an agent row tied to an agency."""
    if user.role != UserRole.AGENCY_ADMIN:
        raise HTTPException(status_code=403, detail="Agentlik rəhbəri tələb olunur")
    agent = await _user_agent(db, user)
    if agent is None or agent.agency_id is None:
        raise HTTPException(status_code=403, detail="Agentlik tapılmadı")
    agency = await db.get(Agency, agent.agency_id)
    if agency is None:
        raise HTTPException(status_code=403, detail="Agentlik tapılmadı")
    return agency


@router.get("", response_model=list[AgencyRead])
async def list_agencies(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
) -> list[AgencyRead]:
    # For now, allow any authenticated user to list agencies
    stmt = select(Agency).offset(offset).limit(limit)
    result = await db.execute(stmt)
    agencies = result.scalars().all()
    return list(agencies)


@router.post("", response_model=AgencyRead, status_code=status.HTTP_201_CREATED)
async def create_agency(
    payload: AgencyCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AgencyRead:
    # Only admins can create agencies
    _require_admin_or_above(current_user)
    agency = Agency(**payload.model_dump())
    db.add(agency)
    await db.commit()
    await db.refresh(agency)
    return agency


@router.get("/me/analytics", response_model=AgencyAnalyticsRead)
async def agency_analytics(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    days: int = Query(default=30, ge=1, le=365),
) -> AgencyAnalyticsRead:
    """Portfolio analytics for the agency the user belongs to."""
    from datetime import UTC, datetime, timedelta

    from sqlalchemy import func

    from app.models.analytics import AnalyticsEvent
    from app.models.favorite import Favorite
    from app.models.messaging import Conversation, Message
    from app.models.property import Property, PropertyStatus
    from app.schemas.analytics import AgencyAnalyticsRead, AgencyListingPoint

    if current_user.role not in (
        UserRole.AGENT,
        UserRole.AGENCY_ADMIN,
        UserRole.MODERATOR,
        UserRole.ADMIN,
        UserRole.SUPER_ADMIN,
    ):
        raise HTTPException(status_code=403, detail="Agency analytics unavailable")

    agency_id = None
    agency_name = ""
    for record in current_user.agent_records or []:
        if record.agency_id:
            agency_id = record.agency_id
            break
    if agency_id:
        agency = await db.get(Agency, agency_id)
        agency_name = agency.name if agency else ""
    else:
        agency = (
            (await db.execute(select(Agency).limit(1))).scalars().first()
            if current_user.role in (UserRole.ADMIN, UserRole.SUPER_ADMIN)
            else None
        )
        agency_id = agency.id if agency else None
        agency_name = agency.name if agency else ""

    since = datetime.now(UTC) - timedelta(days=days)
    listing_stmt = select(Property)
    if agency_id:
        listing_stmt = listing_stmt.where(Property.agency_id == agency_id)

    listings = (await db.execute(listing_stmt)).scalars().all()
    active = [p for p in listings if p.status == PropertyStatus.ACTIVE.value]
    property_ids = [p.id for p in listings]

    total_views = sum(p.views for p in listings)
    total_favorites = 0
    avg_price = round(sum(p.price for p in active) / len(active), 2) if active else 0.0

    per_property_events: dict[uuid.UUID, dict[str, int]] = {}
    if property_ids:
        favorites_rows = (
            await db.execute(
                select(Favorite.property_id, func.count(Favorite.id)).where(
                    Favorite.property_id.in_(property_ids),
                    Favorite.created_at >= since,
                )
            )
        ).all()
        for pid, count in favorites_rows:
            per_property_events.setdefault(pid, {})["favorites"] = int(count)
            total_favorites += int(count)

        event_rows = (
            await db.execute(
                select(
                    AnalyticsEvent.property_id,
                    AnalyticsEvent.event_type,
                    func.count(AnalyticsEvent.id),
                )
                .where(
                    AnalyticsEvent.property_id.in_(property_ids),
                    AnalyticsEvent.created_at >= since,
                )
                .group_by(AnalyticsEvent.property_id, AnalyticsEvent.event_type)
            )
        ).all()
        for pid, event_type, count in event_rows:
            per_property_events.setdefault(pid, {})[event_type] = int(count)

    message_counts: dict[uuid.UUID, int] = {}
    if property_ids:
        conv_rows = (
            await db.execute(
                select(Conversation.id, Conversation.property_id).where(
                    Conversation.property_id.in_(property_ids)
                )
            )
        ).all()
        if conv_rows:
            conv_ids = [conv_id for conv_id, _ in conv_rows]
            msg_rows = (
                await db.execute(
                    select(Conversation.property_id, func.count(Message.id))
                    .join(Message, Message.conversation_id == Conversation.id)
                    .where(
                        Message.conversation_id.in_(conv_ids),
                        Message.created_at >= since,
                    )
                    .group_by(Conversation.property_id)
                )
            ).all()
            for pid, count in msg_rows:
                message_counts[pid] = int(count)

    total_leads = 0
    ranked = sorted(
        listings,
        key=lambda p: per_property_events.get(p.id, {}).get("property_view", 0),
        reverse=True,
    )
    top_listings: list[AgencyListingPoint] = []
    for prop in ranked[:5]:
        events = per_property_events.get(prop.id, {})
        phone = events.get("phone_reveal", 0)
        whatsapp = events.get("whatsapp_click", 0)
        messages = message_counts.get(prop.id, 0)
        leads = phone + whatsapp + messages
        total_leads += leads
        top_listings.append(
            AgencyListingPoint(
                property_id=prop.id,
                title=prop.title,
                views=events.get("property_view", 0),
                favorites=events.get("favorites", 0),
                phone_reveals=phone,
                messages=messages,
            )
        )

    return AgencyAnalyticsRead(
        agency_id=agency_id,
        agency_name=agency_name,
        days=days,
        listings_count=len(listings),
        total_views=total_views,
        total_favorites=total_favorites,
        total_leads=total_leads,
        avg_price=avg_price,
        top_listings=top_listings,
    )


@router.get("/me/invites", response_model=list[AgencyInviteRead])
async def list_invites(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[AgencyInviteRead]:
    """Invites issued by the caller's agency (agency_admin only)."""
    agency = await _require_agency_admin(db, current_user)
    stmt = (
        select(AgencyInvite)
        .where(AgencyInvite.agency_id == agency.id)
        .order_by(AgencyInvite.created_at.desc())
    )
    return list((await db.execute(stmt)).scalars().all())


@router.post("/me/invites", response_model=AgencyInviteRead, status_code=201)
async def create_invite(
    payload: AgencyInviteCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AgencyInviteRead:
    """Invite someone to join the agency (agency_admin only)."""
    agency = await _require_agency_admin(db, current_user)
    existing = (
        await db.execute(
            select(AgencyInvite).where(
                AgencyInvite.agency_id == agency.id,
                AgencyInvite.email == payload.email.lower(),
                AgencyInvite.status == "pending",
            )
        )
    ).scalar_one_or_none()
    if existing is not None:
        raise HTTPException(status_code=409, detail="Bu emailə gözləyən dəvət var")
    invite = AgencyInvite(
        agency_id=agency.id,
        email=payload.email.lower(),
        role=payload.role,
        token=secrets.token_urlsafe(32),
        created_by=current_user.id,
        expires_at=datetime.now(UTC) + timedelta(days=INVITE_TTL_DAYS),
    )
    db.add(invite)
    await db.commit()
    await db.refresh(invite)
    return invite


@router.delete("/me/invites/{invite_id}", status_code=204)
async def cancel_invite(
    invite_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    agency = await _require_agency_admin(db, current_user)
    invite = await db.get(AgencyInvite, invite_id)
    if invite is None or invite.agency_id != agency.id:
        raise HTTPException(status_code=404, detail="Dəvət tapılmadı")
    await db.delete(invite)
    await db.commit()


@router.post("/invites/{token}/accept", response_model=AgentRead)
async def accept_invite(
    token: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AgentRead:
    """Accept a pending invite: the user joins the agency as agent/admin."""
    invite = (
        await db.execute(select(AgencyInvite).where(AgencyInvite.token == token))
    ).scalar_one_or_none()
    if invite is None:
        raise HTTPException(status_code=404, detail="Dəvət tapılmadı")
    if invite.status != "pending":
        raise HTTPException(status_code=409, detail="Dəvət artıq istifadə olunub")
    if invite.email.lower() != current_user.email.lower():
        raise HTTPException(status_code=403, detail="Bu dəvət sizin emailinizə deyil")
    if invite.expires_at < datetime.now(UTC):
        invite.status = "expired"
        await db.commit()
        raise HTTPException(status_code=410, detail="Dəvətin müddəti bitib")

    agency = await db.get(Agency, invite.agency_id)
    if agency is None:
        raise HTTPException(status_code=404, detail="Agentlik tapılmadı")

    existing = (
        await db.execute(
            select(Agent).where(
                Agent.user_id == current_user.id,
                Agent.agency_id == agency.id,
            )
        )
    ).scalar_one_or_none()
    if existing is None:
        existing = Agent(
            user_id=current_user.id,
            agency_id=agency.id,
            name=current_user.full_name or current_user.email,
            email=current_user.email,
        )
        db.add(existing)
        await db.flush()

    if invite.role == "agency_admin":
        current_user.role = UserRole.AGENCY_ADMIN.value
    elif current_user.role == UserRole.USER:
        current_user.role = UserRole.AGENT.value

    invite.status = "accepted"
    invite.accepted_at = datetime.now(UTC)
    await db.commit()
    await db.refresh(existing)
    return existing


@router.post("/me/import/listings", response_model=AgencyImportResult)
async def import_listings_csv(
    file: UploadFile,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AgencyImportResult:
    """Bulk-import draft listings for the agency from a CSV file.

    Expected headers: title, deal_type, property_type, price, currency,
    rooms, area_total, city, district, address_text, description,
    building_type. Rows are validated per-line; failures are collected
    without aborting the import.
    """
    agency = await _require_agency_admin(db, current_user)
    agent = await _user_agent(db, current_user)

    raw = await file.read()
    if len(raw) > 2 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Fayl 2MB-dan böyükdür")
    text = raw.decode("utf-8-sig", errors="replace")
    reader = csv.DictReader(io.StringIO(text))
    if reader.fieldnames is None:
        raise HTTPException(status_code=400, detail="CSV faylı oxuna bilmədi")

    repo = PropertyRepository(db)
    imported = 0
    skipped = 0
    errors: list[dict] = []
    required = {"title", "deal_type", "property_type", "price", "area_total"}
    for row_number, row in enumerate(reader, start=2):
        try:
            missing = required - set(row.keys())
            if missing:
                raise ValueError(f"çatışmayan sütunlar: {', '.join(sorted(missing))}")
            price = float(row.get("price") or 0)
            if price <= 0:
                raise ValueError("price müsbət rəqəm olmalıdır")
            payload = PropertyCreate(
                title=str(row["title"]).strip()[:300],
                description=str(row.get("description") or "").strip(),
                deal_type=str(row["deal_type"]).strip().lower(),
                property_type=str(row["property_type"]).strip().lower(),
                price=price,
                currency=str(row.get("currency") or "AZN").strip().upper(),
                rooms=int(float(row.get("rooms") or 0)),
                area_total=float(row["area_total"]),
                building_type=(str(row["building_type"]).strip().lower() or None),
                owner_id=current_user.id,
                agency_id=agency.id,
                agent_id=agent.id if agent else None,
                location={
                    "latitude": 0.0,
                    "longitude": 0.0,
                    "address_text": str(row.get("address_text") or "").strip(),
                    "city": str(row.get("city") or "").strip() or None,
                    "district": str(row.get("district") or "").strip() or None,
                },
            )
            await repo.create(payload)
            await db.commit()
            imported += 1
        except Exception as exc:  # noqa: BLE001 - per-row isolation
            await db.rollback()
            skipped += 1
            errors.append({"row": row_number, "error": str(exc)[:200]})

    return AgencyImportResult(imported=imported, skipped=skipped, errors=errors)


@router.get("/{agency_id}", response_model=AgencyRead)
async def get_agency(
    agency_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AgencyRead:
    result = await db.execute(select(Agency).where(Agency.id == agency_id))
    agency = result.scalar_one_or_none()
    if not agency:
        raise HTTPException(status_code=404, detail="Agency not found")
    return agency


@router.get("/{agency_id}/public", response_model=dict)
async def get_agency_public_profile(
    agency_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_optional_user),
) -> dict:
    """Public agency profile with its active listings and agents."""
    result = await db.execute(select(Agency).where(Agency.id == agency_id))
    agency = result.scalar_one_or_none()
    if not agency:
        raise HTTPException(status_code=404, detail="Agency not found")

    params = PropertyQueryParams(agency_id=agency_id, page=1, page_size=24)
    listings = await PropertyRepository(db).list(params)
    agents_result = await db.execute(select(Agent).where(Agent.agency_id == agency_id))
    agents = agents_result.scalars().all()
    return {
        "agency": AgencyRead.model_validate(agency),
        "listings": listings,
        "agents": [AgentRead.model_validate(a) for a in agents],
        "is_favorite": False,
    }


@router.patch("/{agency_id}", response_model=AgencyRead)
async def update_agency(
    agency_id: uuid.UUID,
    payload: AgencyUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AgencyRead:
    _require_admin_or_above(current_user)
    result = await db.execute(select(Agency).where(Agency.id == agency_id))
    agency = result.scalar_one_or_none()
    if not agency:
        raise HTTPException(status_code=404, detail="Agency not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(agency, field, value)
    await db.commit()
    await db.refresh(agency)
    return agency


@router.delete(
    "/{agency_id}", status_code=status.HTTP_204_NO_CONTENT, response_model=None
)
async def delete_agency(
    agency_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    _require_admin_or_above(current_user)
    result = await db.execute(select(Agency).where(Agency.id == agency_id))
    agency = result.scalar_one_or_none()
    if not agency:
        raise HTTPException(status_code=404, detail="Agency not found")
    await db.delete(agency)
    await db.commit()
