import uuid
from datetime import UTC, datetime
from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies.auth import (
    can_edit_property,
    get_current_user,
    get_optional_user,
)
from app.core.config import get_settings
from app.core.rate_limit import RateLimiter
from app.core.storage import upload_file
from app.db.session import get_db
from app.models.analytics import AnalyticsEvent
from app.models.appointment import ViewingAppointment
from app.models.enums import PropertyStatus, UserRole
from app.models.favorite import Favorite
from app.models.messaging import Conversation, Message
from app.models.property import Property, PropertyMedia, PropertyPriceHistory
from app.models.user import User
from app.repositories.property import PropertyRepository
from app.schemas.analytics import ListingAnalyticsRead
from app.schemas.common import PaginatedResponse
from app.schemas.property import (
    PropertyCreate,
    PropertyQueryParams,
    PropertyRead,
    PropertySummaryRead,
    PropertyUpdate,
)

router = APIRouter(prefix="/properties", tags=["properties"])

settings = get_settings()

AUTO_PUBLISH_ROLES = (
    UserRole.AGENT,
    UserRole.AGENCY_ADMIN,
    UserRole.MODERATOR,
    UserRole.ADMIN,
    UserRole.SUPER_ADMIN,
)

# Statuses a non-staff owner may set directly via PATCH.
OWNER_ALLOWED_STATUSES = {
    PropertyStatus.DRAFT,
    PropertyStatus.ARCHIVED,
    PropertyStatus.SOLD,
    PropertyStatus.RENTED,
    PropertyStatus.EXPIRED,
}


def _repo(db: AsyncSession) -> PropertyRepository:
    return PropertyRepository(db)


def _now() -> datetime:
    return datetime.now(UTC)


async def _get_property_or_404(
    repo: PropertyRepository, property_id: uuid.UUID
) -> Property:
    prop = await repo.get_by_id(property_id)
    if prop is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Elan tapılmadı",
        )
    return prop


@router.get("", response_model=PaginatedResponse[PropertySummaryRead])
async def list_properties(
    params: Annotated[PropertyQueryParams, Query()],
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[PropertySummaryRead]:
    """Search listings with filters, bounding box, sorting and pagination."""
    return await _repo(db).list(params)


@router.get("/mine", response_model=list[PropertySummaryRead])
async def list_my_properties(
    status_filter: PropertyStatus | None = Query(default=None, alias="status"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[PropertySummaryRead]:
    """The current user's own listings across all statuses (dashboard)."""
    return await _repo(db).list_mine(user.id, status_filter)


@router.get(
    "/{property_id}",
    response_model=PropertyRead,
    responses={404: {"description": "Not found"}},
)
async def get_property(
    property_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_optional_user),
) -> PropertyRead:
    prop = await _get_property_or_404(_repo(db), property_id)
    prop.views += 1
    db.add(
        AnalyticsEvent(
            user_id=current_user.id if current_user else None,
            property_id=property_id,
            event_type="property_view",
            payload={"source": "detail"},
        )
    )
    await db.commit()
    prop = await _get_property_or_404(_repo(db), property_id)
    return _repo(db).to_read(prop)


phone_reveal_limiter = RateLimiter(
    "rl:phone-reveal",
    limit=10,
    window_seconds=3600,
    burst_limit=20,
)


@router.post("/{property_id}/phone-reveal", status_code=status.HTTP_204_NO_CONTENT)
async def phone_reveal(
    property_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_optional_user),
) -> None:
    prop = await _get_property_or_404(_repo(db), property_id)
    if prop.owner_id == (current_user.id if current_user else None):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot reveal your own listing",
        )
    if not await phone_reveal_limiter.is_allowed(prop.owner_id.hex):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many phone reveals for this listing",
        )
    db.add(
        AnalyticsEvent(
            user_id=current_user.id if current_user else None,
            property_id=property_id,
            event_type="phone_reveal",
            payload={"owner_id": str(prop.owner_id)},
        )
    )
    await db.commit()


@router.get(
    "/{property_id}/similar",
    response_model=list[PropertySummaryRead],
)
async def get_similar_properties(
    property_id: uuid.UUID,
    limit: int = Query(default=4, ge=1, le=12),
    db: AsyncSession = Depends(get_db),
) -> list[PropertySummaryRead]:
    repo = _repo(db)
    prop = await _get_property_or_404(repo, property_id)
    return await repo.similar(prop, limit)


@router.post(
    "",
    response_model=PropertyRead,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"description": "Invalid payload"},
        422: {"description": "Validation error"},
    },
)
async def create_property(
    payload: PropertyCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PropertyRead:
    repo = _repo(db)

    if user.role not in AUTO_PUBLISH_ROLES and payload.status != PropertyStatus.DRAFT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Yalnız qaralama kimi yaradıla bilər. Dərc üçün elanı "
            "təsdiqə göndərin.",
        )
    # Derive ownership from authenticated user; ignore any owner_id in payload.
    payload.owner_id = user.id

    try:
        prop = await repo.create(payload)
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Yaradılma mümkün olmadı: dublikat məlumat ola bilməz.",
        ) from exc
    return repo.to_read(prop)


@router.post(
    "/{property_id}/submit",
    response_model=PropertyRead,
    responses={404: {"description": "Not found"}},
)
async def submit_property(
    property_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PropertyRead:
    """Send a draft to moderation, or publish directly for trusted roles."""
    repo = _repo(db)
    prop = await _get_property_or_404(repo, property_id)
    if not can_edit_property(prop, user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu elanı idarə edə bilməzsiniz",
        )
    if prop.status not in (PropertyStatus.DRAFT, PropertyStatus.REJECTED):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Yalnız qaralama və ya rədd edilmiş elan təsdiqə "
            f"göndərilə bilər (hazırki: {prop.status})",
        )

    auto_publish = user.role in AUTO_PUBLISH_ROLES or user.is_verified
    if auto_publish:
        prop.status = PropertyStatus.ACTIVE.value
        prop.published_at = prop.published_at or _now()
    else:
        prop.status = PropertyStatus.PENDING_REVIEW.value
    await db.commit()
    return repo.to_read(await repo.get_by_id(prop.id))  # type: ignore[arg-type]


@router.patch(
    "/{property_id}",
    response_model=PropertyRead,
    responses={404: {"description": "Not found"}},
)
async def update_property(
    property_id: uuid.UUID,
    payload: PropertyUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PropertyRead:
    repo = _repo(db)
    prop = await _get_property_or_404(repo, property_id)
    if not can_edit_property(prop, user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu elanı redaktə edə bilməzsiniz",
        )
    if (
        payload.status is not None
        and user.role not in AUTO_PUBLISH_ROLES
        and payload.status not in OWNER_ALLOWED_STATUSES
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Statusu birbaşa dəyişə bilməzsiniz — elanı təsdiqə göndərməlisiniz",
        )
    # Store the old price for comparison
    old_price = prop.price
    try:
        prop = await repo.update(prop, payload)
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Yeniləmə mümkün olmadı: məlumat uyğunsuzluğu var.",
        ) from exc
    # If the price has changed and a price was provided, create a price history record
    if payload.price is not None and payload.price != old_price:
        price_history = PropertyPriceHistory(
            property_id=prop.id,
            price=payload.price,
        )
        db.add(price_history)
        await db.commit()
    return repo.to_read(prop)


@router.delete(
    "/{property_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={404: {"description": "Not found"}},
)
async def delete_property(
    property_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    repo = _repo(db)
    prop = await _get_property_or_404(repo, property_id)
    if not can_edit_property(prop, user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu elanı silə bilməzsiniz",
        )
    await repo.delete(prop)
    await db.commit()


@router.post(
    "/{property_id}/media",
    response_model=list[PropertyRead],
    status_code=status.HTTP_201_CREATED,
)
async def upload_property_media(
    property_id: uuid.UUID,
    files: list[UploadFile] = File(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[PropertyRead]:
    """Upload one or more images for a property."""
    repo = _repo(db)
    prop = await _get_property_or_404(repo, property_id)
    if not can_edit_property(prop, user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu elanı idarə edə bilməzsiniz",
        )
    if not files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Heç bir fayl yüklənməди",
        )
    from app.models.enums import MediaKind

    uploaded_media = []
    for file in files:
        content = await file.read()
        url = upload_file(content, file.filename, file.content_type)
        media = PropertyMedia(
            property_id=prop.id,
            url=url,
            alt=file.filename or "",
            is_cover=False,
            kind=MediaKind.IMAGE,
        )
        db.add(media)
        uploaded_media.append(media)
    await db.commit()
    for media in uploaded_media:
        await db.refresh(media)
    return [repo.to_read(prop)]


@router.get("/{property_id}/analytics", response_model=ListingAnalyticsRead)
async def get_listing_analytics(
    property_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ListingAnalyticsRead:
    """Per-listing engagement analytics (owner or staff only)."""
    repo = _repo(db)
    prop = await _get_property_or_404(repo, property_id)
    if not can_edit_property(prop, current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu elanın analitikasına baxa bilməzsiniz",
        )

    async def _count(event_type: str) -> int:
        stmt = select(func.count(AnalyticsEvent.id)).where(
            AnalyticsEvent.property_id == property_id,
            AnalyticsEvent.event_type == event_type,
        )
        return (await db.execute(stmt)).scalar() or 0

    favorites = (
        (await db.execute(
            select(func.count(Favorite.id)).where(Favorite.property_id == property_id)
        )).scalar()
        or 0
    )
    messages = (
        (await db.execute(
            select(func.count(Message.id)).where(
                Message.conversation_id.in_(
                    select(Conversation.id).where(
                        Conversation.property_id == property_id
                    )
                )
            )
        )).scalar()
        or 0
    )
    viewing_requests = (
        (await db.execute(
            select(func.count(ViewingAppointment.id)).where(
                ViewingAppointment.property_id == property_id
            )
        )).scalar()
        or 0
    )
    return ListingAnalyticsRead(
        property_id=property_id,
        views=prop.views,
        favorites=favorites,
        phone_reveals=await _count("phone_reveal"),
        whatsapp_clicks=await _count("whatsapp_click"),
        messages=messages,
        viewing_requests=viewing_requests,
    )
