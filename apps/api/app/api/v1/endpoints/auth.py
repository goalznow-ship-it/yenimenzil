from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies.auth import get_current_user, verify_origin
from app.core.config import get_settings
from app.core.rate_limit import RateLimiter
from app.core.security import (
    REFRESH_TOKEN_COOKIE,
    clear_auth_cookies,
    create_access_token,
    generate_refresh_token,
    get_client_ip,
    hash_password,
    hash_refresh_token,
    set_auth_cookies,
    verify_password,
)
from app.db.session import get_db
from app.models.auth import RefreshToken
from app.models.enums import UserRole
from app.models.user import Profile, User
from app.schemas.auth import AuthSuccess, LoginRequest, RegisterRequest, UserRead

router = APIRouter(prefix="/auth", tags=["auth"])

settings = get_settings()

login_limiter = RateLimiter(
    "rl:login",
    limit=settings.RATE_LIMIT_LOGIN_PER_MINUTE,
    window_seconds=60,
    burst_limit=settings.RATE_LIMIT_LOGIN_BURST,
)
register_limiter = RateLimiter(
    "rl:register",
    limit=settings.RATE_LIMIT_LOGIN_PER_MINUTE,
    window_seconds=60,
    burst_limit=settings.RATE_LIMIT_LOGIN_BURST,
)


async def _issue_tokens(
    db: AsyncSession, user: User, request: Request, response: Response
) -> None:
    access_token = create_access_token(str(user.id))
    raw_refresh = generate_refresh_token()
    db.add(
        RefreshToken(
            user_id=user.id,
            token_hash=hash_refresh_token(raw_refresh),
            expires_at=datetime.now(UTC)
            + timedelta(days=settings.REFRESH_TOKEN_TTL_DAYS),
            user_agent=(request.headers.get("user-agent") or "")[:255],
            ip_address=get_client_ip(request),
        )
    )
    await db.flush()
    set_auth_cookies(response, access_token, raw_refresh)


async def _revoke_refresh_token(db: AsyncSession, raw_refresh: str) -> None:
    token_hash = hash_refresh_token(raw_refresh)
    result = await db.execute(
        select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    )
    token = result.scalar_one_or_none()
    if token is not None and token.revoked_at is None:
        token.revoked_at = datetime.now(UTC)


def _user_response(user: User) -> UserRead:
    return UserRead.model_validate(user)


@router.post(
    "/register",
    response_model=AuthSuccess,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(verify_origin)],
)
async def register(
    payload: RegisterRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> AuthSuccess:
    if settings.RATE_LIMIT_ENABLED:
        key = get_client_ip(request) or "unknown"
        if not await register_limiter.is_allowed(key):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many attempts, try again later",
            )

    existing = await db.execute(
        select(User).where(
            (User.email == payload.email.lower())
            | ((User.phone.is_not(None)) & (User.phone == payload.phone))
        )
    )
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email or phone already registered",
        )

    user = User(
        email=payload.email.lower(),
        phone=payload.phone,
        password_hash=hash_password(payload.password),
        full_name=payload.full_name.strip(),
        role=UserRole.USER.value,
    )
    user.profile = Profile()
    db.add(user)
    await db.flush()
    await _issue_tokens(db, user, request, response)
    await db.commit()
    await db.refresh(user)
    return AuthSuccess(user=_user_response(user))


@router.post(
    "/login",
    response_model=AuthSuccess,
    dependencies=[Depends(verify_origin)],
)
async def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> AuthSuccess:
    if settings.RATE_LIMIT_ENABLED:
        key = get_client_ip(request) or "unknown"
        if not await login_limiter.is_allowed(key):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many attempts, try again later",
            )

    result = await db.execute(
        select(User).where(User.email == payload.email.lower())
    )
    user = result.scalar_one_or_none()
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Account is disabled"
        )

    await _issue_tokens(db, user, request, response)
    await db.commit()
    return AuthSuccess(user=_user_response(user))


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> Response:
    raw_refresh = request.cookies.get(REFRESH_TOKEN_COOKIE)
    if raw_refresh:
        await _revoke_refresh_token(db, raw_refresh)
        await db.commit()
    clear_auth_cookies(response)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/refresh",
    response_model=AuthSuccess,
    dependencies=[Depends(verify_origin)],
)
async def refresh(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> AuthSuccess:
    raw_refresh = request.cookies.get(REFRESH_TOKEN_COOKIE)
    if not raw_refresh:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing refresh token",
        )

    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.token_hash == hash_refresh_token(raw_refresh)
        )
    )
    token = result.scalar_one_or_none()
    if (
        token is None
        or token.revoked_at is not None
        or token.expires_at < datetime.now(UTC)
    ):
        clear_auth_cookies(response)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token invalid or expired",
        )

    user = await db.get(User, token.user_id)
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found"
        )

    token.revoked_at = datetime.now(UTC)
    await _issue_tokens(db, user, request, response)
    await db.commit()
    return AuthSuccess(user=_user_response(user))


@router.get("/me", response_model=UserRead)
async def me(
    user: User = Depends(get_current_user),
) -> UserRead:
    return _user_response(user)
