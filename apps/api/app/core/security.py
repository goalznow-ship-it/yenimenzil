"""Password hashing, JWT access tokens and cookie helpers."""

from __future__ import annotations

import hashlib
import secrets
from datetime import UTC, datetime, timedelta

import bcrypt
import jwt
from fastapi import HTTPException, Request, status

from app.core.config import get_settings

settings = get_settings()

ACCESS_TOKEN_COOKIE = "access_token"
REFRESH_TOKEN_COOKIE = "refresh_token"


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        return False


def hash_refresh_token(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def generate_refresh_token() -> str:
    return secrets.token_urlsafe(48)


def create_access_token(user_id: str) -> str:
    now = datetime.now(UTC)
    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": now + timedelta(minutes=settings.API_ACCESS_TOKEN_TTL_MINUTES),
        "type": "access",
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")


def decode_access_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
    except jwt.ExpiredSignatureError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired"
        ) from exc
    except jwt.InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        ) from exc


def set_auth_cookies(response, access_token: str, refresh_token: str) -> None:
    _set_cookie(
        response,
        ACCESS_TOKEN_COOKIE,
        access_token,
        settings.API_ACCESS_TOKEN_TTL_MINUTES * 60,
    )
    _set_cookie(
        response,
        REFRESH_TOKEN_COOKIE,
        refresh_token,
        settings.REFRESH_TOKEN_TTL_DAYS * 86400,
    )


def clear_auth_cookies(response) -> None:
    _set_cookie(response, ACCESS_TOKEN_COOKIE, "", 0)
    _set_cookie(response, REFRESH_TOKEN_COOKIE, "", 0)


def _set_cookie(response, name: str, value: str, max_age: int) -> None:
    response.set_cookie(
        key=name,
        value=value,
        max_age=max_age,
        path="/",
        secure=settings.COOKIE_SECURE,
        httponly=True,
        samesite="lax",
        domain=settings.COOKIE_DOMAIN,
    )


def get_client_ip(request: Request) -> str | None:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client is not None:
        return request.client.host
    return None
