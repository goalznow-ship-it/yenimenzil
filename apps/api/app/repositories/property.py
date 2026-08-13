"""Data-access layer for Property listings.

All query logic (filters, spatial bounding box, sorting, eager loading, and
shaping of the summary rows) lives here so the endpoint stays thin.
"""

from __future__ import annotations

import math
import uuid
from datetime import UTC, datetime

from geoalchemy2 import Geography
from geoalchemy2.shape import WKTElement
from sqlalchemy import Select, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.agency import Agent
from app.models.enums import PropertyStatus, SellerKind
from app.models.favorite import Favorite
from app.models.property import (
    Property,
    PropertyFeature,
    PropertyFeatureItem,
    PropertyLocation,
    PropertyMedia,
    PropertyPriceHistory,
)
from app.models.user import User
from app.schemas.common import PaginatedResponse, PaginationMeta
from app.schemas.property import (
    PropertyCreate,
    PropertyLocationRead,
    PropertyMediaRead,
    PropertyPriceHistoryRead,
    PropertyQueryParams,
    PropertyRead,
    PropertySellerRead,
    PropertySort,
    PropertySummaryRead,
    PropertyUpdate,
)

AZ_MAP = str.maketrans(
    {
        "ə": "e",
        "ş": "s",
        "ğ": "g",
        "ç": "c",
        "ö": "o",
        "ü": "u",
        "ı": "i",
        "Ə": "E",
        "Ş": "S",
        "Ğ": "G",
        "Ç": "C",
        "Ö": "O",
        "Ü": "U",
        "İ": "I",
    }
)


def normalize_az(value: str) -> str:
    return value.lower().translate(AZ_MAP)


def _enum(value):
    """Return the raw value for a StrEnum or the value itself."""
    return value.value if hasattr(value, "value") else value


def _summary_load_options():
    return (
        selectinload(Property.location),
        selectinload(Property.media),
        selectinload(Property.price_history),
        selectinload(Property.owner).selectinload(User.profile),
        selectinload(Property.agency),
        selectinload(Property.agent).selectinload(Agent.agency),
        # eager-load seller properties so active_listings never triggers a
        # lazy load (which raises MissingGreenlet under asyncio)
        selectinload(Property.owner).selectinload(User.properties),
        selectinload(Property.agent).selectinload(Agent.properties),
    )


def _detail_load_options():
    return (
        *_summary_load_options(),
        selectinload(Property.features),
    )


def _slugify(value: str) -> str:
    normalized = normalize_az(value)
    out = []
    for ch in normalized:
        if ch.isalnum():
            out.append(ch)
        elif ch in (" ", "-", "_", "/"):
            out.append("-")
    slug = "".join(out).strip("-")
    return slug[:240] or "listing"


def _apply_filters(
    stmt: Select[tuple[Property]], params: PropertyQueryParams
) -> Select[tuple[Property]]:
    stmt = stmt.where(Property.status == PropertyStatus.ACTIVE)
    stmt = stmt.where(Property.deal_type == params.deal)

    if params.city and params.city != "all":
        stmt = stmt.where(PropertyLocation.city == params.city)

    if params.district and params.district != "all":
        needle = normalize_az(params.district)
        like = f"%{needle}%"
        translated = func.translate(
            func.lower(PropertyLocation.district), "əşğçöüı", "esgcouii"
        )
        translated_neigh = func.translate(
            func.lower(PropertyLocation.neighborhood), "əşğçöüı", "esgcouii"
        )
        translated_settl = func.translate(
            func.lower(PropertyLocation.settlement), "əşğçöüı", "esgcouii"
        )
        translated_landmark = func.translate(
            func.lower(PropertyLocation.landmark), "əşğçöüı", "esgcouii"
        )
        stmt = stmt.where(
            or_(
                translated.like(like),
                translated_neigh.like(like),
                translated_settl.like(like),
                translated_landmark.like(like),
            )
        )

    if params.property_type and params.property_type != "all":
        stmt = stmt.where(Property.property_type == params.property_type)

    if params.rooms:
        room_conds = []
        for r in params.rooms:
            if r >= 4:
                room_conds.append(Property.rooms >= 4)
            elif r == 0:
                room_conds.append(Property.rooms == 0)
            else:
                room_conds.append(Property.rooms == r)
        if room_conds:
            stmt = stmt.where(or_(*room_conds))

    if params.min_price is not None:
        stmt = stmt.where(Property.price >= params.min_price)
    if params.max_price is not None:
        stmt = stmt.where(Property.price <= params.max_price)

    if params.min_area is not None:
        stmt = stmt.where(Property.area_total >= params.min_area)
    if params.max_area is not None:
        stmt = stmt.where(Property.area_total <= params.max_area)

    if params.metro:
        stmt = stmt.where(PropertyLocation.metro == params.metro)

    if params.landmark:
        stmt = stmt.where(PropertyLocation.landmark.ilike(f"%{params.landmark}%"))

    if params.building_type is not None:
        stmt = stmt.where(Property.building_type == params.building_type)

    if params.repair_status is not None:
        stmt = stmt.where(Property.repair_status == params.repair_status)

    if params.owner_only:
        stmt = stmt.where(Property.seller_kind == SellerKind.OWNER.value)

    if params.seller_kind is not None:
        stmt = stmt.where(Property.seller_kind == params.seller_kind)

    if params.agent_id is not None:
        stmt = stmt.where(Property.agent_id == params.agent_id)

    if params.agency_id is not None:
        stmt = stmt.where(Property.agency_id == params.agency_id)

    if params.verified_only:
        stmt = stmt.where(Property.is_verified.is_(True))

    if params.promoted_only:
        stmt = stmt.where(
            or_(Property.is_promoted.is_(True), Property.is_premium.is_(True))
        )

    if params.price_dropped:
        sub = (
            select(PropertyPriceHistory.property_id)
            .group_by(PropertyPriceHistory.property_id)
            .having(func.count(PropertyPriceHistory.id) >= 2)
        )
        latest_sub = select(
            PropertyPriceHistory.property_id,
            func.row_number()
            .over(
                partition_by=PropertyPriceHistory.property_id,
                order_by=PropertyPriceHistory.recorded_at.desc(),
            )
            .label("rn"),
            PropertyPriceHistory.price.label("latest_price"),
        ).subquery()
        first_sub = select(
            PropertyPriceHistory.property_id,
            func.row_number()
            .over(
                partition_by=PropertyPriceHistory.property_id,
                order_by=PropertyPriceHistory.recorded_at.asc(),
            )
            .label("rn"),
            PropertyPriceHistory.price.label("first_price"),
        ).subquery()
        dropped_ids = (
            select(latest_sub.c.property_id)
            .join(
                first_sub,
                (first_sub.c.property_id == latest_sub.c.property_id)
                & (first_sub.c.rn == 1),
            )
            .where(latest_sub.c.rn == 1)
            .where(latest_sub.c.latest_price < first_sub.c.first_price)
        )
        stmt = stmt.where(Property.id.in_(dropped_ids))

    if params.mortgage is not None:
        stmt = stmt.where(Property.mortgage_available.is_(params.mortgage))

    if params.furnished is not None:
        stmt = stmt.where(Property.furnished.is_(params.furnished))

    if params.heating:
        stmt = stmt.where(Property.heating.ilike(f"%{params.heating}%"))

    if params.document_type is not None:
        stmt = stmt.where(Property.document_type == params.document_type)

    if params.floor is not None:
        stmt = stmt.where(Property.floor == params.floor)

    if params.is_first_floor:
        stmt = stmt.where(Property.floor == 1)

    if params.is_last_floor:
        stmt = stmt.where(Property.floor == Property.total_floors)

    if params.total_floors is not None:
        stmt = stmt.where(Property.total_floors == params.total_floors)

    if params.min_bedrooms is not None:
        stmt = stmt.where(Property.bedrooms >= params.min_bedrooms)
    if params.max_bedrooms is not None:
        stmt = stmt.where(Property.bedrooms <= params.max_bedrooms)

    if params.min_bathrooms is not None:
        stmt = stmt.where(Property.bathrooms >= params.min_bathrooms)
    if params.max_bathrooms is not None:
        stmt = stmt.where(Property.bathrooms <= params.max_bathrooms)

    if params.min_area_land is not None:
        stmt = stmt.where(Property.area_land >= params.min_area_land)
    if params.max_area_land is not None:
        stmt = stmt.where(Property.area_land <= params.max_area_land)

    if params.min_construction_year is not None:
        stmt = stmt.where(Property.construction_year >= params.min_construction_year)
    if params.max_construction_year is not None:
        stmt = stmt.where(Property.construction_year <= params.max_construction_year)

    if params.keyword:
        keyword = f"%{params.keyword}%"
        stmt = stmt.where(
            or_(
                Property.title.ilike(keyword),
                Property.description.ilike(keyword),
                Property.reference_code.ilike(keyword),
            )
        )

    if params.published_after is not None:
        stmt = stmt.where(Property.published_at >= params.published_after)

    if params.features:
        sub = (
            select(PropertyFeatureItem.property_id)
            .join(PropertyFeature, PropertyFeature.id == PropertyFeatureItem.feature_id)
            .where(PropertyFeature.code.in_(params.features))
            .group_by(PropertyFeatureItem.property_id)
            .having(func.count(PropertyFeatureItem.feature_id) == len(params.features))
        )
        stmt = stmt.where(Property.id.in_(sub))

    # Map bounding box via PostGIS ST_Intersects on the geography point.
    # The envelope from ST_MakeEnvelope is geometry (SRID 4326); PostGIS casts
    # it to geography implicitly so the comparison uses geodesic math.
    if (
        params.north is not None
        and params.south is not None
        and params.east is not None
        and params.west is not None
    ):
        envelope = func.ST_MakeEnvelope(
            params.west, params.south, params.east, params.north, 4326
        )
        stmt = stmt.where(
            func.ST_Intersects(
                PropertyLocation.point,
                func.cast(envelope, Geography(geometry_type="POLYGON", srid=4326)),
            )
        )

    return stmt


def _apply_sort(stmt: Select[tuple[Property]], sort: PropertySort) -> Select:
    # Always tie-break by id for deterministic pagination.
    if sort == PropertySort.PRICE_ASC:
        return stmt.order_by(Property.price.asc(), Property.id.asc())
    if sort == PropertySort.PRICE_DESC:
        return stmt.order_by(Property.price.desc(), Property.id.asc())
    if sort == PropertySort.PRICE_PER_M2_ASC:
        return stmt.order_by(
            (Property.price / Property.area_total).asc(), Property.id.asc()
        )
    if sort == PropertySort.PRICE_PER_M2_DESC:
        return stmt.order_by(
            (Property.price / Property.area_total).desc(), Property.id.asc()
        )
    if sort == PropertySort.AREA_ASC:
        return stmt.order_by(Property.area_total.asc(), Property.id.asc())
    if sort == PropertySort.AREA_DESC:
        return stmt.order_by(Property.area_total.desc(), Property.id.asc())
    if sort == PropertySort.VIEWS:
        return stmt.order_by(Property.views.desc(), Property.id.asc())
    if sort == PropertySort.FAVORITES:
        fav_count = (
            select(func.count(Favorite.id))
            .where(Favorite.property_id == Property.id)
            .correlate(Property)
            .scalar_subquery()
        )
        return stmt.order_by(fav_count.desc(), Property.id.asc())
    if sort == PropertySort.OLDEST:
        return stmt.order_by(
            Property.published_at.asc().nullsfirst(), Property.id.asc()
        )
    # NEWEST (default): published_at desc, nulls last, deterministic tie-break
    return stmt.order_by(Property.published_at.desc().nullslast(), Property.id.asc())


class PropertyRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # ------------------------------------------------------------------ read

    async def list(
        self, params: PropertyQueryParams
    ) -> PaginatedResponse[PropertySummaryRead]:
        filtered = select(Property).join(Property.location, isouter=False)
        filtered = _apply_filters(filtered, params)

        count_stmt = _apply_filters(
            select(func.count(Property.id))
            .select_from(Property)
            .join(Property.location, isouter=False),
            params,
        )
        total = (await self.session.execute(count_stmt)).scalar_one()

        filtered = _apply_sort(filtered, params.sort)
        filtered = filtered.offset((params.page - 1) * params.page_size).limit(
            params.page_size
        )
        filtered = filtered.options(*_summary_load_options())

        result = await self.session.execute(filtered)
        items = result.scalars().all()

        data = [self._to_summary_read(p) for p in items]
        pages = math.ceil(total / params.page_size) if total else 0
        return PaginatedResponse(
            data=data,
            meta=PaginationMeta(
                page=params.page,
                page_size=params.page_size,
                total=total,
                pages=pages,
            ),
        )

    async def get_by_reference(self, reference_code: str) -> Property | None:
        result = await self.session.execute(
            select(Property)
            .where(Property.reference_code == reference_code)
            .options(*_detail_load_options())
        )
        return result.scalar_one_or_none()

    async def list_mine(
        self, user_id: uuid.UUID, status: PropertyStatus | None = None
    ) -> list[PropertySummaryRead]:
        """All of a user's listings across statuses (dashboard)."""
        stmt = select(Property).join(Property.location, isouter=False)
        stmt = stmt.where(Property.owner_id == user_id)
        if status is not None:
            stmt = stmt.where(Property.status == status)
        stmt = stmt.order_by(Property.updated_at.desc())
        stmt = stmt.options(*_summary_load_options())
        result = await self.session.execute(stmt)
        return [self._to_summary_read(p) for p in result.scalars().all()]

    async def get_by_id(self, property_id: uuid.UUID) -> Property | None:
        result = await self.session.execute(
            select(Property)
            .where(Property.id == property_id)
            .options(*_detail_load_options())
        )
        return result.scalar_one_or_none()

    async def increment_views(self, property_id: uuid.UUID) -> None:
        prop = await self.get_by_id(property_id)
        if prop is not None:
            prop.views += 1
            await self.session.flush()

    async def similar(
        self, prop: Property, limit: int = 4
    ) -> list[PropertySummaryRead]:
        stmt = select(Property).join(Property.location, isouter=False)
        stmt = stmt.where(Property.status == PropertyStatus.ACTIVE)
        stmt = stmt.where(Property.id != prop.id)
        stmt = stmt.where(Property.deal_type == prop.deal_type)
        stmt = stmt.where(Property.property_type == prop.property_type)
        stmt = stmt.order_by(
            func.abs(Property.price - prop.price).asc(), Property.id.asc()
        ).limit(limit)
        stmt = stmt.options(*_summary_load_options())
        result = await self.session.execute(stmt)
        return [self._to_summary_read(p) for p in result.scalars().all()]

    # ------------------------------------------------------------------ write

    async def create(self, payload: PropertyCreate) -> Property:
        reference_code, slug = await self._next_reference_and_slug(payload.title)
        now = datetime.now(UTC)
        prop = Property(
            reference_code=reference_code,
            slug=slug,
            owner_id=payload.owner_id,
            agency_id=payload.agency_id,
            agent_id=payload.agent_id,
            seller_kind=_enum(payload.seller_kind),
            deal_type=_enum(payload.deal_type),
            property_type=_enum(payload.property_type),
            status=_enum(payload.status),
            currency=_enum(payload.currency),
            title=payload.title,
            description=payload.description,
            price=payload.price,
            rooms=payload.rooms,
            bedrooms=payload.bedrooms,
            bathrooms=payload.bathrooms,
            area_total=payload.area_total,
            area_living=payload.area_living,
            area_land=payload.area_land,
            floor=payload.floor,
            total_floors=payload.total_floors,
            building_type=_enum(payload.building_type)
            if payload.building_type
            else None,
            repair_status=_enum(payload.repair_status)
            if payload.repair_status
            else None,
            document_type=_enum(payload.document_type)
            if payload.document_type
            else None,
            mortgage_available=payload.mortgage_available,
            furnished=payload.furnished,
            heating=payload.heating,
            construction_year=payload.construction_year,
            is_verified=payload.is_verified,
            is_premium=payload.is_premium,
            is_promoted=payload.is_promoted,
            published_at=now if payload.status == PropertyStatus.ACTIVE else None,
        )
        prop.location = PropertyLocation(
            latitude=payload.location.latitude,
            longitude=payload.location.longitude,
            point=WKTElement(
                f"SRID=4326;POINT({payload.location.longitude} {payload.location.latitude})",
                srid=4326,
            ),
            address_text=payload.location.address_text,
            city=payload.location.city,
            district=payload.location.district,
            settlement=payload.location.settlement,
            neighborhood=payload.location.neighborhood,
            metro=payload.location.metro,
            landmark=payload.location.landmark,
            street=payload.location.street,
        )
        for i, m in enumerate(payload.media):
            prop.media.append(
                PropertyMedia(
                    kind="image",
                    url=m.url,
                    alt=m.alt,
                    placeholder=m.placeholder,
                    sort_order=m.sort_order or i,
                    is_cover=m.is_cover or (i == 0),
                )
            )
        for ph in payload.price_history:
            prop.price_history.append(
                PropertyPriceHistory(
                    price=ph.price,
                    recorded_at=ph.recorded_at or now,
                )
            )
        if not payload.price_history:
            prop.price_history.append(
                PropertyPriceHistory(price=payload.price, recorded_at=now)
            )
        await self._replace_features(prop, payload.features)

        self.session.add(prop)
        await self.session.flush()
        await self.session.refresh(prop, attribute_names=["created_at", "updated_at"])
        return await self.get_by_id(prop.id)  # type: ignore[return-value]

    async def update(self, prop: Property, payload: PropertyUpdate) -> Property:
        data = payload.model_dump(exclude_unset=True)

        scalar_fields = [
            "title",
            "description",
            "deal_type",
            "property_type",
            "price",
            "currency",
            "rooms",
            "bedrooms",
            "bathrooms",
            "area_total",
            "area_living",
            "area_land",
            "floor",
            "total_floors",
            "building_type",
            "repair_status",
            "document_type",
            "mortgage_available",
            "furnished",
            "heating",
            "construction_year",
            "status",
            "seller_kind",
            "is_verified",
            "is_premium",
            "is_promoted",
            "agency_id",
            "agent_id",
        ]
        for field in scalar_fields:
            if field in data:
                value = data[field]
                if hasattr(value, "value"):
                    value = value.value
                setattr(prop, field, value)

        if "status" in data and data["status"] is not None:
            status_value = data["status"]
            if hasattr(status_value, "value"):
                status_value = status_value.value
            if (
                status_value == PropertyStatus.ACTIVE.value
                and prop.published_at is None
            ):
                prop.published_at = datetime.now(UTC)

        if "edit_count" in data or any(
            k in data
            for k in ("title", "description", "price", "status", "property_type")
        ):
            prop.edit_count = (prop.edit_count or 0) + 1
            prop.last_edited_at = datetime.now(UTC)

        if "location" in data and data["location"] is not None:
            loc = payload.location
            assert loc is not None
            if prop.location is not None:
                prop.location.latitude = loc.latitude
                prop.location.longitude = loc.longitude
                prop.location.point = WKTElement(
                    f"SRID=4326;POINT({loc.longitude} {loc.latitude})", srid=4326
                )
                prop.location.address_text = loc.address_text
                prop.location.city = loc.city
                prop.location.district = loc.district
                prop.location.settlement = loc.settlement
                prop.location.neighborhood = loc.neighborhood
                prop.location.metro = loc.metro
                prop.location.landmark = loc.landmark
                prop.location.street = loc.street

        if "media" in data and data["media"] is not None:
            prop.media.clear()
            await self.session.flush()
            for i, m in enumerate(payload.media or []):
                prop.media.append(
                    PropertyMedia(
                        kind="image",
                        url=m.url,
                        alt=m.alt,
                        placeholder=m.placeholder,
                        sort_order=m.sort_order or i,
                        is_cover=m.is_cover or (i == 0),
                    )
                )

        if "features" in data and data["features"] is not None:
            await self._replace_features(prop, payload.features or [])

        await self.session.flush()
        return await self.get_by_id(prop.id)  # type: ignore[return-value]

    async def delete(self, prop: Property) -> None:
        await self.session.delete(prop)
        await self.session.flush()

    # ------------------------------------------------------------- internal

    async def _next_reference_and_slug(self, title: str) -> tuple[str, str]:
        """Generate a unique AB<span> reference code and matching slug."""
        result = await self.session.execute(
            select(func.max(Property.reference_code)).where(
                Property.reference_code.like("AB%")
            )
        )
        last = result.scalar_one_or_none()
        seq = 1001
        if last and last[2:].isdigit():
            seq = int(last[2:]) + 1
        ref = f"AB{seq}"
        slug = f"{_slugify(title)}-{seq}"
        # Ensure uniqueness
        while True:
            clash = await self.session.execute(
                select(Property.id).where(
                    or_(Property.reference_code == ref, Property.slug == slug)
                )
            )
            if clash.scalar_one_or_none() is None:
                break
            seq += 1
            ref = f"AB{seq}"
            slug = f"{_slugify(title)}-{seq}"
        return ref, slug

    async def _replace_features(self, prop: Property, codes: list[str]) -> None:
        if not codes:
            prop.features.clear()
            return
        result = await self.session.execute(
            select(PropertyFeature).where(PropertyFeature.code.in_(codes))
        )
        features = list(result.scalars().all())
        prop.features = features

    # -------------------------------------------------------------- shaping

    def _seller_read(self, prop: Property) -> PropertySellerRead:
        owner = prop.owner
        agent = prop.agent
        profile = owner.profile if owner is not None else None

        if agent is not None:
            kind = SellerKind.AGENT
            name = agent.name
            agency_name = agent.agency.name if agent.agency is not None else None
            avatar_url = agent.avatar_url
            phone = agent.phone
            verified_phone = agent.verified_phone
            verified_identity = agent.verified_identity
            member_since = (
                agent.member_since.year if agent.member_since is not None else None
            )
            active_listings = sum(
                1 for p in (agent.properties or []) if p.status == PropertyStatus.ACTIVE
            )
            seller_id = agent.id
        else:
            kind = SellerKind.OWNER if owner is not None else SellerKind.AGENCY
            name = owner.full_name if owner is not None else None
            if name is None and prop.agency is not None:
                name = prop.agency.name
                kind = SellerKind.AGENCY
            agency_name = prop.agency.name if prop.agency is not None else None
            avatar_url = profile.avatar_url if profile is not None else None
            phone = owner.phone if owner is not None else None
            verified_phone = bool(profile and profile.phone_verified)
            verified_identity = bool(profile and profile.identity_verified)
            member_since = (
                profile.member_since.year if profile and profile.member_since else None
            )
            active_listings = sum(
                1 for p in (owner.properties or []) if p.status == PropertyStatus.ACTIVE
            )
            seller_id = (
                owner.id
                if owner is not None
                else (prop.agency.id if prop.agency else prop.owner_id)
            )

        return PropertySellerRead(
            id=seller_id,
            name=name or "Elan sahibi",
            kind=kind,
            agency_name=agency_name,
            avatar_url=avatar_url,
            phone=phone,
            verified_phone=verified_phone,
            verified_identity=verified_identity,
            member_since=str(member_since) if member_since else None,
            active_listings=active_listings,
        )

    def _to_summary_read(self, prop: Property) -> PropertySummaryRead:
        cover = next((m for m in prop.media if m.is_cover), None)
        if cover is None and prop.media:
            cover = prop.media[0]
        price_history_sorted = sorted(prop.price_history, key=lambda ph: ph.recorded_at)
        has_price_drop = (
            len(price_history_sorted) >= 2
            and price_history_sorted[-1].price < price_history_sorted[0].price
        )
        price_per_sqm = (
            round(float(prop.price) / float(prop.area_total))
            if prop.area_total
            else None
        )
        return PropertySummaryRead(
            id=prop.id,
            reference_code=prop.reference_code,
            slug=prop.slug,
            title=prop.title,
            deal_type=prop.deal_type,
            property_type=prop.property_type,
            building_type=prop.building_type,
            repair_status=prop.repair_status,
            price=float(prop.price),
            currency=prop.currency,
            price_per_sqm=price_per_sqm,
            rooms=prop.rooms,
            area_total=float(prop.area_total),
            floor=prop.floor,
            total_floors=prop.total_floors,
            is_verified=prop.is_verified,
            is_premium=prop.is_premium,
            is_promoted=prop.is_promoted,
            promotion_tier=prop.promotion_tier,
            promotion_expires_at=prop.promotion_expires_at,
            status=prop.status,
            published_at=prop.published_at,
            city=prop.location.city if prop.location else None,
            district=prop.location.district if prop.location else None,
            address_text=prop.location.address_text if prop.location else None,
            metro=prop.location.metro if prop.location else None,
            latitude=prop.location.latitude if prop.location else None,
            longitude=prop.location.longitude if prop.location else None,
            cover_image=cover.url if cover else None,
            image_count=len(prop.media),
            has_price_drop=has_price_drop,
            seller=self._seller_read(prop),
        )

    def to_summary_read(self, prop: Property) -> PropertySummaryRead:
        return self._to_summary_read(prop)

    def to_read(self, prop: Property) -> PropertyRead:
        summary = self._to_summary_read(prop)
        location = None
        if prop.location is not None:
            location = PropertyLocationRead.model_validate(prop.location)
        media = [PropertyMediaRead.model_validate(m) for m in prop.media]
        price_history = [
            PropertyPriceHistoryRead.model_validate(ph) for ph in prop.price_history
        ]
        return PropertyRead(
            **summary.model_dump(),
            description=prop.description,
            bedrooms=prop.bedrooms,
            bathrooms=prop.bathrooms,
            area_living=float(prop.area_living)
            if prop.area_living is not None
            else None,
            area_land=float(prop.area_land) if prop.area_land is not None else None,
            document_type=prop.document_type,
            mortgage_available=prop.mortgage_available,
            furnished=prop.furnished,
            heating=prop.heating,
            construction_year=prop.construction_year,
            seller_kind=prop.seller_kind,
            owner_id=prop.owner_id,
            agency_id=prop.agency_id,
            agent_id=prop.agent_id,
            views=prop.views,
            created_at=prop.created_at,
            updated_at=prop.updated_at,
            features=[f.code for f in prop.features],
            location=location,
            media=media,
            price_history=price_history,
        )
