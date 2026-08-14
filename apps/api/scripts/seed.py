"""Seed the database with the frontend demo listings.

Usage (from apps/api):

    make seed
    # or
    .venv/bin/python -m scripts.seed [--db-url postgresql+asyncpg://...]

The demo data lives in scripts/demo_listings.json, extracted from
apps/web/src/data/listings.ts by scripts/extract-demo.mjs. The seed is
idempotent: every run wipes the listing/seller tables and re-creates them
from the JSON, so re-seeding always yields the same AB1001..AB10NN set.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import re
import uuid
from datetime import UTC, date, datetime
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

import app.models  # noqa: F401  (register all models on Base.metadata)
from app.core.config import get_settings
from app.models.agency import Agency, Agent
from app.models.enums import FeatureKind, SellerKind
from app.models.property import PropertyFeature
from app.models.user import Profile, User
from app.repositories.property import PropertyRepository
from app.schemas.property import PropertyCreate

DEMO_DATA = Path(__file__).with_name("demo_listings.json")

# Frontend labels (packages/types FEATURE_LABELS) for the catalog rows.
FEATURE_LABELS: dict[str, str] = {
    "extract": "Çıxarış",
    "mortgage": "İpoteka",
    "gas": "Qaz",
    "water": "Su",
    "electricity": "İşıq",
    "central_heating": "Mərkəzi istilik",
    "kombi": "Kombi",
    "air_conditioning": "Kondisioner",
    "elevator": "Lift",
    "security": "Mühafizə",
    "parking": "Parkinq",
    "balcony": "Balkon",
    "pool": "Hovuz",
    "garden": "Həyət",
    "furnished": "Mebel",
    "internet": "İnternet",
    "home_appliances": "Məişət texnikası",
    "children_playground": "Uşaq meydançası",
}

TRUNCATE_TABLES = (
    "property_feature_items",
    "property_price_history",
    "property_media",
    "property_locations",
    "properties",
    "property_features",
    "favorites",
    "agents",
    "agencies",
    "profiles",
    "users",
)


def _parse_year(value: str | None) -> date | None:
    if not value:
        return None
    match = re.match(r"\d{4}", value)
    if not match:
        return None
    return date(int(match.group()), 1, 1)


def _slugify(name: str) -> str:
    az = str.maketrans(
        {"ə": "e", "ş": "s", "ğ": "g", "ç": "c", "ö": "o", "ü": "u", "ı": "i"}
    )
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower().translate(az)).strip("-")
    return slug[:220] or "seller"


class Seed:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.phone_seq = 1000000000

    async def run(self) -> None:
        listings = json.loads(DEMO_DATA.read_text(encoding="utf-8"))
        if not listings:
            raise SystemExit(
                "demo_listings.json is empty — regenerate it with scripts/extract-demo.mjs"
            )

        await self._reset()
        await self._seed_feature_catalog()
        await self._seed_demo_accounts()
        sellers = await self._seed_sellers(listings)
        await self._seed_properties(listings, sellers)

        await self.session.commit()
        print(
            f"Seeded {len(listings)} properties, {len(sellers)} sellers, "
            f"{len(FeatureKind)} feature codes."
        )

    async def _seed_demo_accounts(self) -> None:
        from app.core.security import hash_password
        from app.models.enums import UserRole

        accounts = [
            ("demo@yenimenzil.az", "demo1234", "Demo İstifadəçi", UserRole.USER),
            ("moderator@yenimenzil.az", "moderator1", "Moderator", UserRole.MODERATOR),
            ("admin@yenimenzil.az", "admin1234", "Administrator", UserRole.ADMIN),
        ]
        for email, password, name, role in accounts:
            user = User(
                id=uuid.uuid4(),
                email=email,
                password_hash=hash_password(password),
                full_name=name,
                role=role.value,
                is_verified=True,
            )
            user.profile = Profile(member_since=date(2024, 1, 1))
            self.session.add(user)
        await self.session.flush()

    async def _reset(self) -> None:
        table_list = ", ".join(f'"{t}"' for t in TRUNCATE_TABLES)
        await self.session.execute(
            text(f"TRUNCATE {table_list} RESTART IDENTITY CASCADE")
        )

    async def _seed_feature_catalog(self) -> None:
        for feature in FeatureKind:
            self.session.add(
                PropertyFeature(
                    code=feature.value,
                    label_az=FEATURE_LABELS.get(feature.value, feature.value),
                )
            )
        await self.session.flush()

    async def _seed_sellers(self, listings: list[dict]) -> dict[str, dict]:
        """Create users/agencies/agents for every seller in the demo data."""
        sellers: dict[str, dict] = {}
        by_id: dict[str, dict] = {}
        for listing in listings:
            seller = listing["seller"]
            by_id.setdefault(seller["id"], seller)

        agency_by_name: dict[str, Agency] = {}
        for seller in by_id.values():
            sid = seller["id"]
            email = f"{sid}@demo.yenimenzil.az"
            phone = None
            if seller["kind"] == "owner":
                phone = f"+99450{self.phone_seq}"
                self.phone_seq += 1

            user = User(
                id=uuid.uuid4(),
                email=email,
                phone=phone,
                password_hash="demo-only-no-login",
                full_name=seller["name"],
            )
            self.session.add(user)

            agency: Agency | None = None
            agent: Agent | None = None
            agency_name = seller.get("agencyName")
            if seller["kind"] == "agent" and agency_name:
                agency = agency_by_name.get(agency_name)
                if agency is None:
                    agency = Agency(name=agency_name, slug=_slugify(agency_name))
                    self.session.add(agency)
                    agency_by_name[agency_name] = agency
                agent = Agent(
                    user_id=user.id,
                    agency=agency,
                    name=seller["name"],
                    phone=seller.get("phone"),
                    avatar_url=seller.get("avatarUrl"),
                    verified_phone=bool(seller.get("verifiedPhone")),
                    verified_identity=bool(seller.get("verifiedIdentity")),
                    member_since=_parse_year(seller.get("memberSince")),
                )
                self.session.add(agent)
            elif seller["kind"] == "agency" and agency_name:
                agency = agency_by_name.get(agency_name)
                if agency is None:
                    agency = Agency(
                        name=agency_name,
                        slug=_slugify(agency_name),
                        is_verified=bool(seller.get("verifiedIdentity")),
                    )
                    self.session.add(agency)
                    agency_by_name[agency_name] = agency

            profile = Profile(
                user=user,
                avatar_url=seller.get("avatarUrl"),
                member_since=_parse_year(seller.get("memberSince")),
                phone_verified=bool(seller.get("verifiedPhone")),
                identity_verified=bool(seller.get("verifiedIdentity")),
            )
            self.session.add(profile)

            sellers[sid] = {
                "user_id": user.id,
                "agency_id": agency.id if agency else None,
                "agent_id": agent.id if agent else None,
                "kind": seller["kind"],
            }
            await self.session.flush()
        return sellers

    async def _seed_properties(
        self, listings: list[dict], sellers: dict[str, dict]
    ) -> None:
        repo = PropertyRepository(self.session)
        for listing in listings:
            seller = sellers[listing["seller"]["id"]]
            point = listing["location"]["point"]
            media = []
            for i, image in enumerate(listing.get("images", [])):
                media.append(
                    {
                        "url": image["src"],
                        "alt": image.get("alt"),
                        "placeholder": image.get("placeholder"),
                        "sort_order": i,
                        "is_cover": i == 0,
                    }
                )
            price_history = [
                {
                    "price": entry["price"],
                    "recorded_at": datetime.fromisoformat(entry["date"]),
                }
                for entry in listing.get("priceHistory", [])
            ]
            payload = PropertyCreate(
                owner_id=seller["user_id"],
                agency_id=seller["agency_id"],
                agent_id=seller["agent_id"],
                seller_kind=SellerKind(seller["kind"]),
                deal_type=listing["dealType"],
                property_type=listing["propertyType"],
                price=float(listing["price"]),
                currency=listing["currency"],
                title=listing["title"],
                description=listing["description"],
                rooms=int(listing["rooms"]),
                bedrooms=listing.get("bedrooms"),
                bathrooms=listing.get("bathrooms"),
                area_total=float(listing["areaTotal"]),
                area_living=listing.get("areaLiving"),
                area_land=listing.get("areaLand"),
                floor=listing.get("floor"),
                total_floors=listing.get("totalFloors"),
                building_type=listing.get("buildingType"),
                repair_status=listing.get("repairStatus"),
                document_type=listing.get("documentType"),
                mortgage_available=bool(listing.get("mortgageAvailable")),
                furnished=bool(listing.get("furnished")),
                heating=listing.get("heating"),
                construction_year=listing.get("constructionYear"),
                is_verified=bool(listing.get("isVerified")),
                is_premium=bool(listing.get("isPremium")),
                is_promoted=bool(listing.get("isPromoted")),
                status="active",
                location={
                    "latitude": float(point["lat"]),
                    "longitude": float(point["lng"]),
                    "address_text": listing["location"].get("addressText", ""),
                    "city": listing["location"].get("city"),
                    "district": listing["location"].get("district"),
                    "settlement": listing["location"].get("settlement"),
                    "neighborhood": listing["location"].get("neighborhood"),
                    "metro": listing["location"].get("metro"),
                },
                media=media,
                features=list(listing.get("features", [])),
                price_history=price_history,
            )
            prop = await repo.create(payload)
            prop.views = int(listing.get("views", 0))
            published = listing.get("publishedAt")
            if published:
                prop.published_at = datetime.fromisoformat(published).astimezone(UTC)
            await self.session.flush()


async def main() -> None:
    parser = argparse.ArgumentParser(description="Seed demo listings into the DB")
    parser.add_argument("--db-url", default=None, help="Async SQLAlchemy DB URL")
    args = parser.parse_args()

    db_url = args.db_url or get_settings().DATABASE_URL
    engine = create_async_engine(db_url)
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception as exc:  # pragma: no cover - depends on local infra
        raise SystemExit(
            f"Could not connect to the database ({db_url}). "
            "Start infra with 'make infra-up' and apply migrations with "
            "'make db-migrate'."
        ) from exc

    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    try:
        async with async_session() as session:
            await Seed(session).run()
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
