from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.security_headers import SecurityHeadersMiddleware

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Background tasks on startup/shutdown."""
    # Start expiry watcher task
    from app.services.expiry_watcher import start_expiry_watcher, stop_expiry_watcher

    start_expiry_watcher()
    yield
    stop_expiry_watcher()


def create_app() -> FastAPI:
    application = FastAPI(
        title=settings.APP_NAME,
        version="0.1.0",
        description="Marketplace backend for YeniMenzil.az",
        lifespan=lifespan,
    )

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
