import logging
import uuid
from datetime import UTC, datetime, timedelta
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
from geoalchemy2.shape import WKTElement
from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies.auth import (
    can_edit_property,
    get_current_user,
    get_optional_user,
)
from app.core.config import get_settings
from app.core.rate_limit import RateLimiter
from app.core.storage import delete_file, upload_file
from app.db.session import get_db
from app.models.analytics import AnalyticsEvent
from app.models.appointment import ViewingAppointment
from app.models.enums import PropertyStatus, UserRole
from app.models.favorite import Favorite
from app.models.messaging import Conversation, Message
from app.models.property import (
    Property,
    PropertyLocation,
    PropertyMedia,
    PropertyPriceHistory,
)
from app.models.user import User
from app.repositories.property import PropertyRepository
from app.schemas.analytics import ListingAnalyticsRead
from app.schemas.common import PaginatedResponse
from app.schemas.property import (
    PropertyCreate,
    PropertyMediaReorder,
    PropertyMediaUpdate,
    PropertyQueryParams,
    PropertyRead,
    PropertySummaryRead,
    PropertyUpdate,
)

logger = logging.getLogger(__name__)

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


async def _read_upload_limited(file: UploadFile) -> bytes:
    """Read at most the configured upload limit plus one sentinel byte."""
    max_bytes = settings.MEDIA_MAX_SIZE_MB * 1024 * 1024
    content = await file.read(max_bytes + 1)
    if len(content) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Fayl maksimum {settings.MEDIA_MAX_SIZE_MB} MB ola bilər",
        )
    return content


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
    """Upload one or more images for a property (validated + thumbnails)."""
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
            detail="Heç bir fayl yüklənməyib",
        )
    from app.models.enums import MediaKind
    from app.services.image_processing import make_thumbnail, webp_suffix
    from app.services.media_validator import validate_image_file

    current_count = (
        await db.execute(
            select(func.count(PropertyMedia.id)).where(
                PropertyMedia.property_id == prop.id
            )
        )
    ).scalar() or 0
    if current_count + len(files) > settings.MEDIA_MAX_IMAGES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Maksimum {settings.MEDIA_MAX_IMAGES} şəkil yüklənə bilər",
        )
    has_cover = (
        await db.execute(
            select(PropertyMedia.id)
            .where(
                PropertyMedia.property_id == prop.id,
                PropertyMedia.is_cover.is_(True),
            )
            .limit(1)
        )
    ).scalar_one_or_none() is not None
    uploaded_media = []
    for file in files:
        content = await _read_upload_limited(file)
        valid, error = validate_image_file(content, file.filename or "")
        if not valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error or "Yanlış şəkil faylı",
            )
        url = upload_file(content, file.filename or "image", file.content_type)
        thumbnail_url = None
        thumb = make_thumbnail(content, file.filename or "image")
        if thumb is not None:
            thumb_name = f"{uuid.uuid4().hex}{webp_suffix()}"
            try:
                thumbnail_url = upload_file(thumb, thumb_name, "image/webp")
            except Exception:  # noqa: BLE001 - thumbnails are best-effort
                thumbnail_url = None
        media = PropertyMedia(
            property_id=prop.id,
            url=url,
            thumbnail_url=thumbnail_url,
            alt=file.filename or "",
            is_cover=(not has_cover),
            sort_order=current_count + len(uploaded_media),
            kind=MediaKind.IMAGE,
        )
        if not has_cover:
            has_cover = True
        db.add(media)
        uploaded_media.append(media)
    await db.commit()
    db.expire(prop, ["media"])
    return [repo.to_read(await repo.get_by_id(prop.id))]  # type: ignore[arg-type]


@router.patch(
    "/{property_id}/media/{media_id}",
    response_model=list[PropertyRead],
)
async def update_property_media(
    property_id: uuid.UUID,
    media_id: uuid.UUID,
    payload: PropertyMediaUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[PropertyRead]:
    """Update media metadata: alt, sort order, and/or set as cover image."""
    repo = _repo(db)
    prop = await _get_property_or_404(repo, property_id)
    if not can_edit_property(prop, user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu elanı idarə edə bilməzsiniz",
        )
    media = await db.get(PropertyMedia, media_id)
    if media is None or media.property_id != prop.id:
        raise HTTPException(status_code=404, detail="Media not found")
    if payload.is_cover is True:
        await db.execute(
            update(PropertyMedia)
            .where(
                PropertyMedia.property_id == prop.id,
                PropertyMedia.is_cover.is_(True),
            )
            .values(is_cover=False)
        )
        media.is_cover = True
    if payload.alt is not None:
        media.alt = payload.alt
    if payload.sort_order is not None:
        media.sort_order = payload.sort_order
    await db.commit()
    db.expire(prop, ["media"])
    return [repo.to_read(await repo.get_by_id(prop.id))]  # type: ignore[arg-type]


@router.delete(
    "/{property_id}/media/{media_id}",
    response_model=list[PropertyRead],
)
async def delete_property_media(
    property_id: uuid.UUID,
    media_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[PropertyRead]:
    """Delete a media item. If it was the cover, promote the next image."""
    repo = _repo(db)
    prop = await _get_property_or_404(repo, property_id)
    if not can_edit_property(prop, user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu elanı idarə edə bilməzsiniz",
        )
    media = await db.get(PropertyMedia, media_id)
    if media is None or media.property_id != prop.id:
        raise HTTPException(status_code=404, detail="Media not found")
    was_cover = media.is_cover
    await db.delete(media)
    if was_cover:
        next_media = await db.execute(
            select(PropertyMedia)
            .where(PropertyMedia.property_id == prop.id)
            .order_by(PropertyMedia.sort_order)
            .limit(1)
        )
        next_item = next_media.scalar_one_or_none()
        if next_item is not None:
            next_item.is_cover = True
    await db.commit()
    try:
        delete_file(media.url)
        if media.thumbnail_url:
            delete_file(media.thumbnail_url)
    except Exception:
        logger.warning("Failed to clean up deleted media objects", exc_info=True)
    db.expire(prop, ["media"])
    return [repo.to_read(await repo.get_by_id(prop.id))]  # type: ignore[arg-type]


@router.put(
    "/{property_id}/media/{media_id}",
    response_model=list[PropertyRead],
)
async def replace_property_media(
    property_id: uuid.UUID,
    media_id: uuid.UUID,
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[PropertyRead]:
    """Replace the file of an existing media item (validated + re-thumbnailed)."""
    from app.services.image_processing import make_thumbnail, webp_suffix
    from app.services.media_validator import validate_image_file

    repo = _repo(db)
    prop = await _get_property_or_404(repo, property_id)
    if not can_edit_property(prop, user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu elanı idarə edə bilməzsiniz",
        )
    media = await db.get(PropertyMedia, media_id)
    if media is None or media.property_id != prop.id:
        raise HTTPException(status_code=404, detail="Media not found")
    content = await _read_upload_limited(file)
    valid, error = validate_image_file(content, file.filename or "")
    if not valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error or "Yanlış şəkil faylı",
        )
    old_url = media.url
    old_thumb = media.thumbnail_url
    media.url = upload_file(content, file.filename or "image", file.content_type)
    thumbnail_url = None
    thumb = make_thumbnail(content, file.filename or "image")
    if thumb is not None:
        thumb_name = f"{uuid.uuid4().hex}{webp_suffix()}"
        try:
            thumbnail_url = upload_file(thumb, thumb_name, "image/webp")
        except Exception:  # noqa: BLE001 - thumbnails are best-effort
            thumbnail_url = None
    media.thumbnail_url = thumbnail_url
    await db.commit()
    try:
        delete_file(old_url)
        if old_thumb:
            delete_file(old_thumb)
    except Exception:
        logger.warning("Failed to clean up old media objects", exc_info=True)
    db.expire(prop, ["media"])
    return [repo.to_read(await repo.get_by_id(prop.id))]  # type: ignore[arg-type]


@router.post(
    "/{property_id}/media/reorder",
    response_model=list[PropertyRead],
)
async def reorder_property_media(
    property_id: uuid.UUID,
    payload: PropertyMediaReorder,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[PropertyRead]:
    """Reorder media by providing the ordered list of media ids."""
    repo = _repo(db)
    prop = await _get_property_or_404(repo, property_id)
    if not can_edit_property(prop, user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu elanı idarə edə bilməzsiniz",
        )
    existing = await db.execute(
        select(PropertyMedia).where(PropertyMedia.property_id == prop.id)
    )
    by_id = {m.id: m for m in existing.scalars().all()}
    if set(payload.media_ids) != set(by_id.keys()):
        raise HTTPException(
            status_code=400, detail="Media id list must match all listing media"
        )
    for index, media_id in enumerate(payload.media_ids):
        by_id[media_id].sort_order = index
    await db.commit()
    db.expire(prop, ["media"])
    return [repo.to_read(await repo.get_by_id(prop.id))]  # type: ignore[arg-type]


@router.post("/{property_id}/duplicate", response_model=PropertyRead)
async def duplicate_property(
    property_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PropertyRead:
    """Clone an existing listing into a new draft (media included)."""
    repo = _repo(db)
    prop = await _get_property_or_404(repo, property_id)
    if not can_edit_property(prop, user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu elanı surətləşdirə bilməzsiniz",
        )
    reference_code, slug = await repo._next_reference_and_slug(f"{prop.title} (surət)")
    now = _now()
    clone = Property(
        reference_code=reference_code,
        slug=slug,
        owner_id=user.id,
        agency_id=prop.agency_id,
        agent_id=prop.agent_id,
        seller_kind=prop.seller_kind,
        deal_type=prop.deal_type,
        property_type=prop.property_type,
        status=PropertyStatus.DRAFT.value,
        currency=prop.currency,
        title=f"{prop.title} (surət)",
        description=prop.description,
        price=prop.price,
        rooms=prop.rooms,
        bedrooms=prop.bedrooms,
        bathrooms=prop.bathrooms,
        area_total=prop.area_total,
        area_living=prop.area_living,
        area_land=prop.area_land,
        floor=prop.floor,
        total_floors=prop.total_floors,
        building_type=prop.building_type,
        repair_status=prop.repair_status,
        document_type=prop.document_type,
        mortgage_available=prop.mortgage_available,
        furnished=prop.furnished,
        heating=prop.heating,
        construction_year=prop.construction_year,
        created_at=now,
        updated_at=now,
    )
    if prop.location is not None:
        loc = prop.location
        clone.location = PropertyLocation(
            latitude=loc.latitude,
            longitude=loc.longitude,
            point=WKTElement(
                f"SRID=4326;POINT({loc.longitude} {loc.latitude})", srid=4326
            ),
            address_text=loc.address_text,
            city=loc.city,
            district=loc.district,
            settlement=loc.settlement,
            neighborhood=loc.neighborhood,
            metro=loc.metro,
            landmark=loc.landmark,
            street=loc.street,
        )
    for m in prop.media:
        clone.media.append(
            PropertyMedia(
                url=m.url,
                thumbnail_url=m.thumbnail_url,
                alt=m.alt,
                placeholder=m.placeholder,
                is_cover=m.is_cover,
                sort_order=m.sort_order,
                kind=m.kind,
            )
        )
    if prop.features:
        clone.features = list(prop.features)
    db.add(clone)
    await db.commit()
    return repo.to_read(await repo.get_by_id(clone.id))  # type: ignore[arg-type]


@router.post("/{property_id}/renew", response_model=PropertyRead)
async def renew_property(
    property_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PropertyRead:
    """Renew an expired/archived listing back into the moderation flow."""
    repo = _repo(db)
    prop = await _get_property_or_404(repo, property_id)
    if not can_edit_property(prop, user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu elanı yeniləyə bilməzsiniz",
        )
    if prop.status not in (
        PropertyStatus.EXPIRED.value,
        PropertyStatus.ARCHIVED.value,
        PropertyStatus.REJECTED.value,
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Yalnız bitmiş/arxivlənmiş/rədd edilmiş elan yenilənə bilər "
            f"(hazırki: {prop.status})",
        )
    prop.status = (
        PropertyStatus.ACTIVE.value
        if (user.role in AUTO_PUBLISH_ROLES or user.is_verified)
        else PropertyStatus.PENDING_REVIEW.value
    )
    prop.published_at = prop.published_at or _now()
    prop.expires_at = _now() + timedelta(days=settings.PROPERTY_LISTING_DAYS)
    await db.commit()
    return repo.to_read(await repo.get_by_id(prop.id))  # type: ignore[arg-type]


@router.post("/{property_id}/deactivate", response_model=PropertyRead)
async def deactivate_property(
    property_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PropertyRead:
    """Deactivate a published listing (archive it)."""
    repo = _repo(db)
    prop = await _get_property_or_404(repo, property_id)
    if not can_edit_property(prop, user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu elanı idarə edə bilməzsiniz",
        )
    if prop.status != PropertyStatus.ACTIVE.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Yalnız aktiv elan dayandırıla bilər",
        )
    prop.status = PropertyStatus.ARCHIVED.value
    await db.commit()
    return repo.to_read(await repo.get_by_id(prop.id))  # type: ignore[arg-type]


@router.post("/{property_id}/reactivate", response_model=PropertyRead)
async def reactivate_property(
    property_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PropertyRead:
    """Reactivate an archived listing (goes through moderation again)."""
    repo = _repo(db)
    prop = await _get_property_or_404(repo, property_id)
    if not can_edit_property(prop, user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu elanı idarə edə bilməzsiniz",
        )
    if prop.status != PropertyStatus.ARCHIVED.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Yalnız arxivlənmiş elan yenidən aktivləşdirilə bilər",
        )
    prop.status = (
        PropertyStatus.ACTIVE.value
        if (user.role in AUTO_PUBLISH_ROLES or user.is_verified)
        else PropertyStatus.PENDING_REVIEW.value
    )
    await db.commit()
    return repo.to_read(await repo.get_by_id(prop.id))  # type: ignore[arg-type]


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
        await db.execute(
            select(func.count(Favorite.id)).where(Favorite.property_id == property_id)
        )
    ).scalar() or 0
    messages = (
        await db.execute(
            select(func.count(Message.id)).where(
                Message.conversation_id.in_(
                    select(Conversation.id).where(
                        Conversation.property_id == property_id
                    )
                )
            )
        )
    ).scalar() or 0
    viewing_requests = (
        await db.execute(
            select(func.count(ViewingAppointment.id)).where(
                ViewingAppointment.property_id == property_id
            )
        )
    ).scalar() or 0
    return ListingAnalyticsRead(
        property_id=property_id,
        views=prop.views,
        favorites=favorites,
        phone_reveals=await _count("phone_reveal"),
        whatsapp_clicks=await _count("whatsapp_click"),
        messages=messages,
        viewing_requests=viewing_requests,
    )
