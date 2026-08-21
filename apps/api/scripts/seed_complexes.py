"""Seed residential complexes for local development."""

import argparse
import asyncio
import uuid
from datetime import UTC, datetime
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

import app.models  # noqa: F401
from app.core.config import get_settings
from app.models.complex import ResidentialComplex


COMPLEXES = [
    {
        "name": "White City",
        "slug": "white-city",
        "developer_name": "White City Development",
        "status": "ready",
        "description": "Premium yaşayış kompleksi Bakı mərkəzində, Dənizkənarı bulvarına yaxın. Müasir arxitektura, hovuz, fitnes mərkəzi, 24/7 mühafizə və qapalı parkinq.",
        "address_text": "Yasamal r., Elmlər Akademiyası metrosu yaxınlığı",
        "city": "Bakı",
        "district": "Yasamal",
        "metro": "Elmlər Akademiyası",
        "latitude": 40.385,
        "longitude": 49.817,
        "completion_year": 2023,
        "total_units": 245,
        "cover_image": "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?auto=format&fit=crop&w=1400&q=80",
        "amenities": ["hovuz", "fitnes mərkəzi", "mühafizə", "qapalı parkinq", "çimərlik", "cafe"],
        "is_verified": True,
    },
    {
        "name": "Caspian Residence",
        "slug": "caspian-residence",
        "developer_name": "Caspian Group",
        "status": "ready",
        "description": "Xəzər dənizinə birbaşa mənzərəli premium yaşayış kompleksi. Hovuz, sauna, tennis kortları, yaşıllıq sahələri və xüsusi sahil stripe.",
        "address_text": "Səbail r., Sahil metrosu yaxınlığı",
        "city": "Bakı",
        "district": "Səbail",
        "metro": "Sahil",
        "latitude": 40.367,
        "longitude": 49.833,
        "completion_year": 2024,
        "total_units": 189,
        "cover_image": "https://images.unsplash.com/photo-1613490493576-7fde63acd811?auto=format&fit=crop&w=1400&q=80",
        "amenities": ["hovuz", "sauna", "tennis", "yaşıllıq", "sahil", "mühafizə", "qapalı parkinq"],
        "is_verified": True,
    },
    {
        "name": "Park Hill",
        "slug": "park-hill",
        "developer_name": "Park Hill Construction",
        "status": "under_construction",
        "description": "Yaşıl zonayaulen müasir kompleks. Geniş yaşıllıq sahələri, uşaq meydançaları, velosiped yolları və kommersiya obyektləri.",
        "address_text": "Nərimanov r., Gənclik metrosu yaxınlığı",
        "city": "Bakı",
        "district": "Nərimanov",
        "metro": "Gənclik",
        "latitude": 40.409,
        "longitude": 49.850,
        "completion_year": 2025,
        "total_units": 156,
        "cover_image": "https://images.unsplash.com/photo-1600210492486-724fe5c67fb0?auto=format&fit=crop&w=1400&q=80",
        "amenities": ["park", "uşaq meydançası", "velosiped yolları", "market", "kafé", "mühafizə"],
        "is_verified": True,
    },
    {
        "name": "Green Gardens",
        "slug": "green-gardens",
        "developer_name": "Green Gardens LLC",
        "status": "announced",
        "description": "Eko-dostu mühitdə, geniş yaşıllıq sahələrinə malik ailəvi yaşayış kompleksi. Enerji səmərəli binalar, güneş panelləri, yağış suyu toplayıcı sistemlər.",
        "address_text": "Xətai r., Neftçilər metrosu yaxınlığı",
        "city": "Bakı",
        "district": "Xətai",
        "metro": "Neftçilər",
        "latitude": 40.371,
        "longitude": 49.855,
        "completion_year": 2026,
        "total_units": 203,
        "cover_image": "https://images.unsplash.com/photo-1600573472550-8090b5e0745e?auto=format&fit=crop&w=1400&q=80",
        "amenities": ["yaşıllıq", "güneş panelləri", "ekoloji", "uşaq meydançası", "mühafizə", "parkinq"],
        "is_verified": False,
    },
    {
        "name": "Sea Breeze",
        "slug": "sea-breeze",
        "developer_name": "Sea Breeze Development",
        "status": "ready",
        "description": "Dənizkənarı yaşayış kompleksi: villa, townhouse və mənzillər. Xüsusi sahil, hendek, yelkən klubu, restoranlar və spa mərkəzi.",
        "address_text": "Xəzər r., Sea Breeze kompleksi",
        "city": "Bakı",
        "district": "Xəzər",
        "metro": None,
        "latitude": 40.493,
        "longitude": 50.030,
        "completion_year": 2024,
        "total_units": 320,
        "cover_image": "https://images.unsplash.com/photo-1560185007-cde436f6a4d0?auto=format&fit=crop&w=1400&q=80",
        "amenities": ["sahil", "hendek", "yelkən klubu", "restoran", "spa", "hovuz", "tennis", "mühafizə"],
        "is_verified": True,
    },
    {
        "name": "Baku Towers",
        "slug": "baku-towers",
        "developer_name": "Baku Towers LLC",
        "status": "under_construction",
        "description": "Bakının ən yüksək yaşayış binalarından biri. Panoramik dəniz və şəhər mənzərəsi, lüks lobbı, konseyer xidməti, sky lounge.",
        "address_text": "Nəsimi r., 28 May metrosu yaxınlığı",
        "city": "Bakı",
        "district": "Nəsimi",
        "metro": "28 May",
        "latitude": 40.380,
        "longitude": 49.847,
        "completion_year": 2026,
        "total_units": 120,
        "cover_image": "https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?auto=format&fit=crop&w=1400&q=80",
        "amenities": ["sky lounge", "konseyer", "fitnes", "hovuz", "mühafizə", "qapalı parkinq", "lüks lobbı"],
        "is_verified": True,
    },
]


async def seed_complexes(db_url: str | None = None) -> None:
    if db_url is None:
        db_url = get_settings().DATABASE_URL
    engine = create_async_engine(db_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # Clear existing complexes
        await session.execute(text('TRUNCATE "residential_complexes" RESTART IDENTITY CASCADE'))
        
        for c in COMPLEXES:
            complex_obj = ResidentialComplex(
                id=uuid.uuid4(),
                name=c["name"],
                slug=c["slug"],
                developer_name=c["developer_name"],
                status=c["status"],
                description=c["description"],
                address_text=c["address_text"],
                city=c["city"],
                district=c["district"],
                metro=c.get("metro"),
                latitude=c["latitude"],
                longitude=c["longitude"],
                completion_year=c["completion_year"],
                total_units=c["total_units"],
                cover_image=c["cover_image"],
                amenities=c["amenities"],
                is_verified=c["is_verified"],
            )
            session.add(complex_obj)
        
        await session.commit()
        print(f"Seeded {len(COMPLEXES)} residential complexes.")

    await engine.dispose()


async def main() -> None:
    parser = argparse.ArgumentParser(description="Seed residential complexes into the DB")
    parser.add_argument("--db-url", default=None, help="Async SQLAlchemy DB URL")
    args = parser.parse_args()

    db_url = args.db_url or get_settings().DATABASE_URL
    await seed_complexes(db_url)


if __name__ == "__main__":
    asyncio.run(main())