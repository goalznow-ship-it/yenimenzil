from typing import Any

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, Response, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.session import get_db
from app.schemas.health import HealthResponse

router = APIRouter(tags=["health"])


async def _readiness(
    db: AsyncSession,
) -> tuple[str, str]:
    settings = get_settings()

    database_status = "ok"
    try:
        await db.execute(text("SELECT 1"))
    except Exception:  # noqa: BLE001 - health check must never raise
        database_status = "unavailable"

    redis_status = "ok"
    try:
        client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
        await client.ping()
        await client.aclose()
    except Exception:  # noqa: BLE001 - health check must never raise
        redis_status = "unavailable"
    return database_status, redis_status


@router.get("/health/live", response_model=HealthResponse)
async def health_live() -> HealthResponse:
    """Liveness: the process is up and serving.

    Dependency status is intentionally NOT checked here and reported as
    ``not_checked`` so this endpoint never falsely claims healthy
    dependencies. Use /health/ready for real dependency verification.
    """
    settings = get_settings()
    return HealthResponse(
        status="ok",
        application=settings.APP_NAME,
        database="not_checked",
        redis="not_checked",
    )


@router.get("/health/ready", response_model=HealthResponse)
async def health_ready(
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> HealthResponse:
    """Readiness: process can serve requests (DB + Redis reachable)."""
    database_status, redis_status = await _readiness(db)
    settings = get_settings()
    if database_status != "ok" or redis_status != "ok":
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return HealthResponse(
        status="ok" if database_status == "ok" and redis_status == "ok" else "degraded",
        application=settings.APP_NAME,
        database=database_status,
        redis=redis_status,
    )


@router.get("/health", response_model=HealthResponse)
async def health(
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> HealthResponse:
    settings = get_settings()

    database_status = "ok"
    try:
        await db.execute(text("SELECT 1"))
    except Exception:  # noqa: BLE001 - health check must never raise
        database_status = "unavailable"

    redis_status = "ok"
    try:
        client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
        await client.ping()
        await client.aclose()
    except Exception:  # noqa: BLE001 - health check must never raise
        redis_status = "unavailable"

    if database_status != "ok" or redis_status != "ok":
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return HealthResponse(
        status="ok" if database_status == "ok" and redis_status == "ok" else "degraded",
        application=settings.APP_NAME,
        database=database_status,
        redis=redis_status,
    )


def build_openapi_info() -> dict[str, Any]:
    return {
        "title": "IdealEv.az API",
        "version": "0.1.0",
        "description": "Marketplace backend for IdealEv.az",
    }
