"""Test configuration.

Uses a dedicated ``yenimenzil_test`` database on the local PostGIS container
(port 5434). The DATABASE_URL env var is set before any app import so the
app's settings/engine bind to the test database.
"""
import asyncio
import os

TEST_DB_NAME = "yenimenzil_test"
TEST_DB_URL = (
    f"postgresql+asyncpg://yenimenzil:yenimenzil@localhost:5434/{TEST_DB_NAME}"
)
ADMIN_DB_URL = "postgresql://yenimenzil:yenimenzil@localhost:5434/yenimenzil"

os.environ["DATABASE_URL"] = TEST_DB_URL

import asyncpg  # noqa: E402
import pytest  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402
from sqlalchemy import text  # noqa: E402
from sqlalchemy.ext.asyncio import create_async_engine  # noqa: E402
from sqlalchemy.pool import NullPool  # noqa: E402

import app.models  # noqa: E402,F401  (register all models on Base.metadata)
from app.db.base import Base  # noqa: E402
from app.db.session import async_session_factory  # noqa: E402
from app.main import app  # noqa: E402

TRUNCATE_TABLES = ", ".join(
    f"\"{t.name}\"" for t in reversed(Base.metadata.sorted_tables)
)


def _run(coro):
    return asyncio.run(coro)


@pytest.fixture(scope="session", autouse=True)
def db_ready():
    """Create the test database and apply the full schema (with PostGIS)."""
    async def prepare() -> None:
        conn = await asyncpg.connect(ADMIN_DB_URL)
        try:
            await conn.execute(f"CREATE DATABASE {TEST_DB_NAME}")
        except asyncpg.exceptions.DuplicateDatabaseError:
            pass
        await conn.close()

        engine = create_async_engine(TEST_DB_URL, poolclass=NullPool)
        async with engine.begin() as conn:
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
            await conn.run_sync(Base.metadata.create_all)
        await engine.dispose()

    _run(prepare())
    yield


@pytest.fixture(autouse=True)
def clean_tables():
    """Truncate every table between tests for full isolation."""
    async def truncate() -> None:
        engine = create_async_engine(TEST_DB_URL, poolclass=NullPool)
        async with engine.begin() as conn:
            await conn.execute(
                text(f"TRUNCATE {TRUNCATE_TABLES} RESTART IDENTITY CASCADE")
            )
        await engine.dispose()

    _run(truncate())
    yield


@pytest.fixture()
async def db():
    async with async_session_factory() as session:
        yield session


@pytest.fixture()
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture()
async def owner(db):
    """A minimal owner user used as the property owner."""
    from app.models.user import User

    user = User(
        email="owner@test.az",
        phone="+994500000001",
        password_hash="not-a-real-hash",
        full_name="Test Sahib",
    )
    db.add(user)
    await db.flush()
    await db.commit()
    return user


@pytest.fixture()
async def feature_catalog(db):
    """Insert the feature codes used across the test suite."""
    from app.models.property import PropertyFeature

    for code in ("elevator", "mortgage", "parking", "balcony", "pool"):
        db.add(PropertyFeature(code=code, label_az=code))
    await db.flush()
    await db.commit()


def make_property_payload(owner_id, **overrides):
    payload = {
        "title": "Test elan 3 otaqli manzil",
        "description": "Gözəl mənzil, mərkəzdə.",
        "deal_type": "sale",
        "property_type": "apartment",
        "price": 150000,
        "currency": "AZN",
        "rooms": 3,
        "bedrooms": 2,
        "bathrooms": 1,
        "area_total": 80,
        "area_living": 62,
        "floor": 5,
        "total_floors": 12,
        "building_type": "new",
        "repair_status": "renovated",
        "document_type": "extract",
        "mortgage_available": True,
        "owner_id": str(owner_id),
        "location": {
            "latitude": 40.4093,
            "longitude": 49.8502,
            "address_text": "Nərimanov r., Gənclik",
            "city": "Bakı",
            "district": "Nərimanov",
            "neighborhood": "Gənclik",
            "metro": "Gənclik",
        },
        "features": ["elevator", "mortgage"],
        "media": [
            {"url": "https://img.test/1.jpg", "alt": "Qonaq otağı", "is_cover": True},
            {"url": "https://img.test/2.jpg", "alt": "Mətbəx"},
        ],
        "price_history": [{"price": 155000}, {"price": 150000}],
    }
    payload.update(overrides)
    return payload
