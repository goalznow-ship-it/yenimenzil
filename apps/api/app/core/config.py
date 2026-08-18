from functools import lru_cache
from pathlib import Path

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[4]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=REPO_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    APP_ENV: str = "development"
    APP_NAME: str = "IdealEv.az API"
    API_V1_PREFIX: str = "/api/v1"

    DATABASE_URL: str = (
        "postgresql+asyncpg://yenimenzil:yenimenzil@localhost:5434/yenimenzil"
    )
    REDIS_URL: str = "redis://localhost:6381/0"

    # Comma-separated list of allowed CORS origins.
    CORS_ORIGINS: str = (
        "http://localhost:3000,http://localhost:3001,"
        "http://127.0.0.1:3000,http://127.0.0.1:3001"
    )

    SECRET_KEY: str = "change-me-in-production"
    API_ACCESS_TOKEN_TTL_MINUTES: int = 15
    REFRESH_TOKEN_TTL_DAYS: int = 30
    COOKIE_SECURE: bool = False
    COOKIE_DOMAIN: str | None = None

    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_LOGIN_PER_MINUTE: int = 10
    RATE_LIMIT_LOGIN_BURST: int = 20

    # Media storage (S3-compatible, e.g. MinIO).
    S3_ENDPOINT: str = "localhost:9002"
    S3_BUCKET: str = "yenimenzil-media"
    S3_ACCESS_KEY: str = "minioadmin"
    S3_SECRET_KEY: str = "minioadmin"
    S3_PUBLIC_URL: str = "http://localhost:9002"
    S3_SECURE: bool = False
    MEDIA_MAX_SIZE_MB: int = 10
    MEDIA_MIN_WIDTH: int = 400
    MEDIA_MAX_IMAGES: int = 15
    MEDIA_THUMB_WIDTH: int = 480
    MEDIA_THUMB_QUALITY: int = 80

    # Payment provider: mock (local dev), stripe (optional production) or manual.
    PAYMENT_PROVIDER: str = "mock"
    # Hard guard: mock payments are never allowed in production unless this
    # is explicitly set to true (local staging only).
    ALLOW_MOCK_PAYMENTS_IN_PROD: bool = False
    STRIPE_PUBLIC_KEY: str = ""
    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    MOCK_PAYMENT_WEBHOOK_SECRET: str = "mock-dev-secret"

    # Listings: how long a published listing stays live before auto-expiry.
    PROPERTY_LISTING_DAYS: int = 60

    # Public-facing base URLs (used for reset/verify links).
    PUBLIC_APP_URL: str = "http://localhost:3000"

    # SMTP (production email is an external credential).
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_USE_TLS: bool = True
    DEFAULT_FROM_EMAIL: str = "no-reply@idealev.az"

    @property
    def cors_origins_list(self) -> list[str]:
        return [
            origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()
        ]

    @model_validator(mode="after")
    def validate_production(self) -> "Settings":
        """Fail fast on genuinely required configuration for production."""
        if self.APP_ENV != "production":
            return self

        if not self.SECRET_KEY or self.SECRET_KEY == "change-me-in-production":
            raise ValueError(
                "SECRET_KEY must be set to a strong random value in production"
            )
        if not self.DATABASE_URL or "localhost" in self.DATABASE_URL:
            raise ValueError(
                "DATABASE_URL must point to the production database in production"
            )
        if not self.CORS_ORIGINS.strip():
            raise ValueError(
                "CORS_ORIGINS must list the production origin in production"
            )
        if "localhost" in self.CORS_ORIGINS:
            raise ValueError(
                "CORS_ORIGINS must not contain localhost origins in production"
            )
        if self.PAYMENT_PROVIDER == "mock" and not self.ALLOW_MOCK_PAYMENTS_IN_PROD:
            raise ValueError(
                "PAYMENT_PROVIDER=mock is forbidden in production. Set a real "
                "provider (stripe/manual) or explicitly allow with "
                "ALLOW_MOCK_PAYMENTS_IN_PROD=true (staging only)."
            )
        if self.PAYMENT_PROVIDER == "stripe" and (
            not self.STRIPE_SECRET_KEY or not self.STRIPE_WEBHOOK_SECRET
        ):
            raise ValueError(
                "STRIPE_SECRET_KEY and STRIPE_WEBHOOK_SECRET are required when "
                "PAYMENT_PROVIDER=stripe in production"
            )
        if not self.S3_ACCESS_KEY or not self.S3_SECRET_KEY:
            raise ValueError("S3 credentials are required in production")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
