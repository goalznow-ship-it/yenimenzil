from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Query

router = APIRouter(prefix="/location", tags=["location"])


@router.get("/hierarchy")
async def get_location_hierarchy(
    country: str = Query("AZ", description="Country code (ISO 3166-1 alpha-2)"),
) -> dict[str, Any]:
    """
    Return the location hierarchy for Azerbaijan.
    For now, we return a hardcoded list of cities and districts.
    In a real application, this would come from a database or a dedicated service.
    """
    # Hardcoded data for Azerbaijan
    hierarchy = {
        "country": "Azərbaycan",
        "country_code": "AZ",
        "regions": [
            {
                "name": "Bakı",
                "type": "city",
                "districts": [
                    {"name": "Nərimanov", "type": "district"},
                    {"name": "Nəsimi", "type": "district"},
                    {"name": "Nizami", "type": "district"},
                    {"name": "Sabail", "type": "district"},
                    {"name": "Sabunçu", "type": "district"},
                    {"name": "Səәr", "type": "district"},
                    {"name": "Xətai", "type": "district"},
                    {"name": "Xəzər", "type": "district"},
                    {"name": "Yasamal", "type": "district"},
                    {"name": "Zəәr", "type": "district"},
                    {"name": "Qaradağ", "type": "district"},
                    {"name": "Qəbələ", "type": "district"},
                    {"name": "Suraxanı", "type": "district"},
                ],
            },
            {
                "name": "Gəncə",
                "type": "city",
                "districts": [
                    {"name": "Kapaz", "type": "district"},
                    {"name": "Nizami", "type": "district"},
                    {"name": "Qaparlı", "type": "district"},
                    {"name": "Xətai", "type": "district"},
                ],
            },
            {
                "name": "Sumqayıt",
                "type": "city",
                "districts": [
                    {"name": "Sumqayıt", "type": "district"},
                ],
            },
        ],
    }

    return hierarchy


@router.get("/landmarks")
async def get_landmarks(
    city: str | None = Query(None, description="City name"),
    district: str | None = Query(None, description="District name"),
) -> list[dict[str, Any]]:
    """
    Return landmarks for a given city or district.
    For now, we return an empty list.
    In a real application, this would come from a database or a dedicated service.
    """
    # Placeholder for landmarks
    return []
