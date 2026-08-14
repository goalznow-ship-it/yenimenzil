from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.location import LocationPlace

router = APIRouter(prefix="/location", tags=["location"])

LOCATION_KINDS = (
    "city",
    "district",
    "settlement",
    "neighborhood",
    "metro",
    "landmark",
    "street",
)


async def _places(
    db: AsyncSession,
    kind: str,
    city: str | None = None,
    district: str | None = None,
    q: str | None = None,
    limit: int = 200,
) -> list[dict[str, Any]]:
    stmt = select(LocationPlace).where(LocationPlace.kind == kind)
    if city:
        stmt = stmt.where(LocationPlace.city == city)
    if district:
        stmt = stmt.where(LocationPlace.district == district)
    if q:
        stmt = stmt.where(LocationPlace.name_az.ilike(f"%{q}%"))
    stmt = stmt.order_by(LocationPlace.sort_order, LocationPlace.name_az).limit(limit)
    rows = (await db.execute(stmt)).scalars().all()
    return [
        {
            "id": str(p.id),
            "name": p.name_az,
            "slug": p.slug,
            "kind": p.kind,
            "city": p.city,
            "district": p.district,
            "metro": p.metro,
            "latitude": p.latitude,
            "longitude": p.longitude,
        }
        for p in rows
    ]


@router.get("/hierarchy")
async def get_location_hierarchy(
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Full Azerbaijan hierarchy: country -> city -> district -> settlements/metros/landmarks."""
    cities = await _places(db, "city", limit=500)
    hierarchy: list[dict[str, Any]] = []
    for city in cities:
        districts = await _places(db, "district", city=city["name"], limit=200)
        hierarchy.append(
            {
                "name": city["name"],
                "slug": city["slug"],
                "type": "city",
                "districts": districts,
            }
        )
    return {
        "country": "Azərbaycan",
        "country_code": "AZ",
        "regions": hierarchy,
    }


@router.get("/cities")
async def get_cities(
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    """All Azerbaijani cities."""
    return await _places(db, "city", limit=500)


@router.get("/districts")
async def get_districts(
    city: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    """Districts, optionally filtered by city."""
    return await _places(db, "district", city=city, limit=500)


@router.get("/settlements")
async def get_settlements(
    city: str | None = Query(None),
    district: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    """Settlements/qəsəbə, optionally filtered by city/district."""
    return await _places(db, "settlement", city=city, district=district, limit=500)


@router.get("/neighborhoods")
async def get_neighborhoods(
    city: str | None = Query(None),
    district: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    """Neighborhoods/məhəllə, optionally filtered by city/district."""
    return await _places(db, "neighborhood", city=city, district=district, limit=500)


@router.get("/metros")
async def get_metros(
    city: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    """Metro stations, optionally filtered by city."""
    return await _places(db, "metro", city=city, limit=500)


@router.get("/landmarks")
async def get_landmarks(
    city: str | None = Query(None),
    district: str | None = Query(None),
    q: str | None = Query(None, description="Name prefix search"),
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    """Popular landmarks (shopping malls, parks, universities, etc.)."""
    return await _places(db, "landmark", city=city, district=district, q=q, limit=500)


@router.get("/streets")
async def get_streets(
    city: str | None = Query(None),
    district: str | None = Query(None),
    q: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    """Streets, optionally filtered by city/district."""
    return await _places(db, "street", city=city, district=district, q=q, limit=500)


@router.get("/search")
async def search_places(
    q: str = Query(..., min_length=1, max_length=120),
    city: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """First-class landmark/metro/district search across the whole catalog.

    Returns grouped results so the frontend can offer typed suggestions for
    district + metro + landmark simultaneously.
    """
    like = f"%{q}%"
    stmt = (
        select(LocationPlace)
        .where(LocationPlace.name_az.ilike(like))
        .order_by(LocationPlace.kind, LocationPlace.sort_order, LocationPlace.name_az)
        .limit(300)
    )
    if city:
        stmt = stmt.where((LocationPlace.city == city) | (LocationPlace.kind == "city"))
    rows = (await db.execute(stmt)).scalars().all()

    grouped: dict[str, list[dict[str, Any]]] = {k: [] for k in LOCATION_KINDS}
    for p in rows:
        grouped[p.kind].append(
            {
                "id": str(p.id),
                "name": p.name_az,
                "slug": p.slug,
                "kind": p.kind,
                "city": p.city,
                "district": p.district,
                "metro": p.metro,
                "latitude": p.latitude,
                "longitude": p.longitude,
            }
        )
    return {"query": q, "results": grouped}
