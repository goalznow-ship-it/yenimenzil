from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[4]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=REPO_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    APP_ENV: str = "development"
    APP_NAME: str = "YeniMenzil.az API"
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

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
