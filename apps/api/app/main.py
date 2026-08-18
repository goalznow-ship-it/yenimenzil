from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.request_context import RequestContextMiddleware
from app.core.security_headers import SecurityHeadersMiddleware

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Async lifespan — start watcher as a background thread task."""
    import asyncio
    from app.services.expiry_watcher import start_expiry_watcher

    # Start the watcher in a daemon thread via asyncio.to_thread.
    # This ensures the coroutine is consumed (not unawaited) within
    # the async context of the lifespan.
    task = asyncio.create_task(asyncio.to_thread(start_expiry_watcher))
    try:
        yield
    finally:
        task.cancel()


def create_app() -> FastAPI:
    application = FastAPI(
        title=settings.APP_NAME,
        version="0.1.0",
        description="Marketplace backend for IdealEv.az",
        lifespan=lifespan,
    )

    application.add_middleware(RequestContextMiddleware)

    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    application.add_middleware(SecurityHeadersMiddleware)

    application.include_router(api_router, prefix=settings.API_V1_PREFIX)

    @application.get("/", include_in_schema=False)
    async def root() -> dict[str, str]:
        return {"application": settings.APP_NAME, "docs": "/docs"}

    return application


app = create_app()
