from __future__ import annotations

import hashlib
import secrets
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import delete, select
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
from app.models.verification import VerificationToken
from app.schemas.auth import AuthSuccess, LoginRequest, RegisterRequest, UserRead
from app.schemas.verification import (
    ForgotPasswordRequest,
    PasswordChangeRequest,
    ResetPasswordRequest,
    VerificationStatusRead,
    VerifyTokenRequest,
)

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


def _hash_token(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


def _send_password_reset_email(to: str, token: str) -> None:
    """Fire-and-forget password reset email; safe without SMTP configured."""
    from app.services.email import send_email

    reset_url = f"{settings.PUBLIC_APP_URL}/reset-password?token={token}"
    send_email(
        to,
        "YeniMenzil.az — Şifrə bərpası",
        (
            f"Şifrənizi bərpa etmək üçün bu linki açın: {reset_url}\n\n"
            "Əgər bu sorğunu siz etməmisinizsə, bu e-poçtu nəzərə almayın."
        ),
    )


def _send_verification_email(to: str, token: str) -> None:
    """Fire-and-forget email verification; safe without SMTP configured."""
    from app.services.email import send_email

    verify_url = f"{settings.PUBLIC_APP_URL}/verify-email?token={token}"
    send_email(
        to,
        "YeniMenzil.az — E-poçt təsdiqi",
        (
            f"E-poçtunuzu təsdiq etmək üçün bu linki açın: {verify_url}\n\n"
            "Əgər qeydiyyatdan siz keçməmisinizsə, bu e-poçtu nəzərə almayın."
        ),
    )


async def _issue_verification_token(
    db: AsyncSession, user: User, kind: str
) -> str:
    # Keep only the newest token of each kind for an account. This both
    # invalidates links replaced by a resend and keeps token storage bounded.
    await db.execute(
        delete(VerificationToken).where(
            VerificationToken.user_id == user.id,
            VerificationToken.kind == kind,
        )
    )
    raw = secrets.token_urlsafe(32)
    db.add(
        VerificationToken(
            user_id=user.id,
            kind=kind,
            token_hash=_hash_token(raw),
            expires_at=datetime.now(UTC) + timedelta(hours=24),
        )
    )
    return raw


async def _issue_phone_code(db: AsyncSession, user: User) -> str:
    """Issue a short-lived numeric phone OTP, stored only as a hash."""
    await db.execute(
        delete(VerificationToken).where(
            VerificationToken.user_id == user.id,
            VerificationToken.kind == "phone",
        )
    )
    raw = f"{secrets.randbelow(1_000_000):06d}"
    db.add(
        VerificationToken(
            user_id=user.id,
            kind="phone",
            token_hash=_hash_token(raw),
            expires_at=datetime.now(UTC) + timedelta(minutes=10),
        )
    )
    return raw


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
    if not user.is_verified:
        verify_token = await _issue_verification_token(db, user, "email")
        await db.commit()
        _send_verification_email(user.email, verify_token)
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

    result = await db.execute(select(User).where(User.email == payload.email.lower()))
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


@router.patch("/password", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
async def change_password(
    payload: PasswordChangeRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    if not verify_password(payload.current_password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )
    user.password_hash = hash_password(payload.new_password)
    # Revoke all refresh tokens so other sessions must log in again
    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.user_id == user.id, RefreshToken.revoked_at.is_(None)
        )
    )
    for token in result.scalars().all():
        token.revoked_at = datetime.now(UTC)
    await db.commit()


@router.post("/forgot-password", status_code=status.HTTP_202_ACCEPTED)
async def forgot_password(
    payload: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Issue a password-reset token. Always returns 202 even if the email
    does not exist (no user enumeration)."""
    result = await db.execute(
        select(User).where(User.email == payload.email.strip().lower())
    )
    user = result.scalar_one_or_none()
    if user is not None:
        token = await _issue_verification_token(db, user, "password_reset")
        await db.commit()
        _send_password_reset_email(user.email, token)
    return {"detail": "If the email exists, a reset link has been issued."}


@router.post(
    "/reset-password", status_code=status.HTTP_204_NO_CONTENT, response_model=None
)
async def reset_password(
    payload: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
) -> None:
    token_hash = _hash_token(payload.token.strip())
    result = await db.execute(
        select(VerificationToken).where(
            VerificationToken.token_hash == token_hash,
            VerificationToken.kind == "password_reset",
        )
    )
    token = result.scalar_one_or_none()
    if (
        token is None
        or token.used_at is not None
        or token.expires_at < datetime.now(UTC)
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset token is invalid or expired",
        )
    user = await db.get(User, token.user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    user.password_hash = hash_password(payload.new_password)
    token.used_at = datetime.now(UTC)
    # Revoke all refresh tokens
    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.user_id == user.id, RefreshToken.revoked_at.is_(None)
        )
    )
    for rt in result.scalars().all():
        rt.revoked_at = datetime.now(UTC)
    await db.commit()


@router.post(
    "/verify-email", status_code=status.HTTP_204_NO_CONTENT, response_model=None
)
async def verify_email(
    payload: VerifyTokenRequest,
    db: AsyncSession = Depends(get_db),
) -> None:
    token_hash = _hash_token(payload.token.strip())
    result = await db.execute(
        select(VerificationToken).where(
            VerificationToken.token_hash == token_hash,
            VerificationToken.kind == "email",
        )
    )
    token = result.scalar_one_or_none()
    if (
        token is None
        or token.used_at is not None
        or token.expires_at < datetime.now(UTC)
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification token is invalid or expired",
        )
    user = await db.get(User, token.user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_verified = True
    token.used_at = datetime.now(UTC)
    await db.commit()


@router.post(
    "/verify-phone", status_code=status.HTTP_204_NO_CONTENT, response_model=None
)
async def verify_phone(
    payload: VerifyTokenRequest,
    db: AsyncSession = Depends(get_db),
) -> None:
    token_hash = _hash_token(payload.token.strip())
    result = await db.execute(
        select(VerificationToken).where(
            VerificationToken.token_hash == token_hash,
            VerificationToken.kind == "phone",
        )
    )
    token = result.scalar_one_or_none()
    if (
        token is None
        or token.used_at is not None
        or token.expires_at < datetime.now(UTC)
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification token is invalid or expired",
        )
    user = await db.get(User, token.user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    if user.profile:
        user.profile.phone_verified = True
    token.used_at = datetime.now(UTC)
    await db.commit()


@router.post("/resend-verification", status_code=status.HTTP_202_ACCEPTED)
async def resend_verification(
    kind: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Issue a new verification token for the current user."""
    if kind not in ("email", "phone"):
        raise HTTPException(status_code=400, detail="Unknown verification kind")
    if kind == "phone" and not user.phone:
        raise HTTPException(status_code=400, detail="Əvvəlcə telefon nömrəsi əlavə edin")
    token = (
        await _issue_phone_code(db, user)
        if kind == "phone"
        else await _issue_verification_token(db, user, kind)
    )
    await db.commit()
    if kind == "email":
        _send_verification_email(user.email, token)
    response = {"detail": "Verification token issued."}
    # Local development has no SMS gateway. Never expose OTPs in production.
    if kind == "phone" and settings.APP_ENV != "production":
        response["dev_code"] = token
    return response


@router.get("/verification-status", response_model=VerificationStatusRead)
async def verification_status(
    user: User = Depends(get_current_user),
) -> VerificationStatusRead:
    profile = user.profile
    return VerificationStatusRead(
        email_verified=user.is_verified,
        phone_verified=bool(profile and profile.phone_verified),
        email_pending=not user.is_verified,
        phone_pending=bool(user.phone and (not profile or not profile.phone_verified)),
        verification_pending=False,
        verification_rejected=False,
    )
