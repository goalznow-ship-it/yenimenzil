"""Listing quality scoring and duplicate-risk detection (Phase 14).

Scores a property 0-100 across completeness, media and location signals,
then flags likely duplicates against active listings and price outliers
versus the local market average.
"""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass, field

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.enums import PropertyStatus
from app.models.property import Property, PropertyLocation


@dataclass
class DuplicateCandidate:
    property_id: uuid.UUID
    title: str
    confidence: float
    reason: str


@dataclass
class QualityReport:
    score: float
    sections: dict[str, dict[str, float]] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    duplicates: list[DuplicateCandidate] = field(default_factory=list)
    market_avg_price_per_m2: float | None = None
    listing_price_per_m2: float | None = None


def _normalize(text: str) -> str:
    return re.sub(r"[^a-z0-9əöüğşıçç]", "", text.lower())


def _tokenize(text: str) -> set[str]:
    tokens = set(_normalize(text).split())
    return {t for t in tokens if len(t) >= 3}


def _text_similarity(a: str, b: str) -> float:
    ta = _tokenize(a)
    tb = _tokenize(b)
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / max(1.0, min(len(ta), len(tb)))


async def _market_price_per_m2(db: AsyncSession, prop: Property) -> float | None:
    """Average price per m² for active listings in the same city/deal."""
    stmt = (
        select(func.sum(Property.price) / func.nullif(func.sum(Property.area_total), 0))
        .join(PropertyLocation, PropertyLocation.property_id == Property.id)
        .where(
            Property.status == PropertyStatus.ACTIVE.value,
            Property.id != prop.id,
            Property.deal_type == prop.deal_type,
            Property.area_total > 0,
            Property.price > 0,
        )
    )
    location = await _location(db, prop)
    if location and location.city:
        stmt = stmt.where(PropertyLocation.city == location.city)
    avg = (await db.execute(stmt)).scalar()
    return float(avg) if avg else None


async def _location(db: AsyncSession, prop: Property) -> PropertyLocation | None:
    return (
        await db.execute(
            select(PropertyLocation).where(PropertyLocation.property_id == prop.id)
        )
    ).scalar_one_or_none()


async def _media_count(db: AsyncSession, prop: Property) -> int:
    from app.models.property import PropertyMedia

    return (
        await db.execute(
            select(func.count(PropertyMedia.id)).where(
                PropertyMedia.property_id == prop.id
            )
        )
    ).scalar() or 0


async def find_duplicates(
    db: AsyncSession, prop: Property, limit: int = 3
) -> list[DuplicateCandidate]:
    """Active listings that are likely duplicates of `prop`."""
    candidates: list[DuplicateCandidate] = []
    location = await _location(db, prop)

    stmt = (
        select(Property)
        .options(selectinload(Property.location))
        .where(
            Property.status == PropertyStatus.ACTIVE.value,
            Property.id != prop.id,
            Property.deal_type == prop.deal_type,
            Property.property_type == prop.property_type,
        )
    )
    if location and location.city:
        stmt = stmt.where(
            PropertyLocation.city == location.city,
            PropertyLocation.property_id == Property.id,
        )
    rows = (await db.execute(stmt)).scalars().all()

    for other in rows:
        reasons: list[str] = []
        if other.price and prop.price:
            ratio = abs(other.price - prop.price) / max(prop.price, 1)
            if ratio <= 0.15:
                reasons.append("qiymət yaxındır")
        if other.rooms and prop.rooms and other.rooms == prop.rooms:
            reasons.append("otaq sayı eynidir")
        if other.area_total and prop.area_total:
            area_ratio = abs(other.area_total - prop.area_total) / max(
                prop.area_total, 1
            )
            if area_ratio <= 0.1:
                reasons.append("sahə eynidir")

        similarity = max(
            _text_similarity(other.title, prop.title),
            _text_similarity(other.description or "", prop.description or ""),
        )
        if similarity >= 0.6:
            reasons.append("mətn oxşardır")

        if not reasons:
            continue
        confidence = round(
            min(
                1.0,
                0.35 * similarity
                + 0.25 * (1 if "qiymət yaxındır" in reasons else 0)
                + 0.2 * (1 if "otaq sayı eynidir" in reasons else 0)
                + 0.2 * (1 if "sahə eynidir" in reasons else 0),
            ),
            2,
        )
        if confidence >= 0.35:
            candidates.append(
                DuplicateCandidate(
                    property_id=other.id,
                    title=other.title,
                    confidence=confidence,
                    reason=", ".join(reasons),
                )
            )
        if len(candidates) >= limit:
            break
    return candidates


async def score_listing(db: AsyncSession, prop: Property) -> QualityReport:
    """Score a property 0-100 and collect warnings + duplicate candidates."""
    sections: dict[str, dict[str, float]] = {}
    warnings: list[str] = []

    # --- completeness (max 60) ---
    completeness = 0.0
    if len((prop.title or "").strip()) >= 10:
        completeness += 10
    else:
        warnings.append("Başlıq çox qısadır (ən azı 10 simvol)")
    if len((prop.description or "").strip()) >= 50:
        completeness += 10
    else:
        warnings.append("Təsvir çox qısadır (ən azı 50 simvol)")
    if prop.price and prop.price > 0:
        completeness += 10
    if prop.rooms and prop.rooms > 0:
        completeness += 10
    if prop.area_total and prop.area_total > 0:
        completeness += 10
    if prop.floor is not None and prop.total_floors:
        completeness += 5
    if prop.building_type or prop.repair_status or prop.document_type:
        completeness += 5
    sections["completeness"] = {"score": completeness, "max": 60}

    # --- media (max 25) ---
    media_count = await _media_count(db, prop)
    if media_count >= 3:
        media_score = 25.0
    elif media_count == 2:
        media_score = 15.0
    elif media_count == 1:
        media_score = 8.0
    else:
        media_score = 0.0
        warnings.append("Elanda şəkil yoxdur")
    if media_count < 3 and media_count > 0:
        warnings.append("Ən azı 3 şəkil tövsiyə olunur")
    sections["media"] = {"score": media_score, "max": 25}

    # --- location (max 15) ---
    location_score = 0.0
    location = await _location(db, prop)
    if location:
        if location.city:
            location_score += 6
        if location.district:
            location_score += 6
        if location.metro or location.street:
            location_score += 3
        if not location.district:
            warnings.append("Rayon göstərilməyib")
    else:
        warnings.append("Yer (şəhər/rayon) göstərilməyib")
    sections["location"] = {"score": location_score, "max": 15}

    score = round(min(100.0, completeness + media_score + location_score), 1)

    market_avg = await _market_price_per_m2(db, prop)
    price_per_m2 = (
        round(float(prop.price) / float(prop.area_total), 2)
        if prop.price and prop.area_total
        else None
    )
    if market_avg and price_per_m2:
        ratio = price_per_m2 / market_avg
        if ratio >= 2.0:
            warnings.append(
                f"Qiymət m² görə bazar ortalamasından {ratio:.1f}× yüksəkdir"
            )
        elif ratio <= 0.4:
            warnings.append(
                "Qiymət m² görə bazar ortalamasından nəzərəçarpacaq dərəcədə aşağıdır"
            )

    duplicates = await find_duplicates(db, prop)
    if duplicates:
        warnings.append(
            f"Oxşar elan(lar) aşkar edildi: {', '.join(d.title[:40] for d in duplicates)}"
        )

    return QualityReport(
        score=score,
        sections=sections,
        warnings=warnings,
        duplicates=duplicates,
        market_avg_price_per_m2=market_avg,
        listing_price_per_m2=price_per_m2,
    )


def report_to_dict(report: QualityReport) -> dict:
    return {
        "score": report.score,
        "sections": report.sections,
        "warnings": report.warnings,
        "duplicates": [
            {
                "property_id": str(d.property_id),
                "title": d.title,
                "confidence": d.confidence,
                "reason": d.reason,
            }
            for d in report.duplicates
        ],
        "market_avg_price_per_m2": report.market_avg_price_per_m2,
        "listing_price_per_m2": report.listing_price_per_m2,
    }
