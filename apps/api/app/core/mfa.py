"""Admin multi-factor authentication (MFA) foundation.

Provides TOTP-based MFA for admin user accounts.
Supports:
- TOTP secret generation and verification
- QR code URI generation for authenticator apps
- Session-based MFA enforcement
- Backup codes
"""

from __future__ import annotations

import base64
import secrets
from datetime import UTC, datetime

from passlib.hash import sha256_crypt

from app.core.config import get_settings

settings = get_settings()

ACCESS_TOKEN_COOKIE = "access_token"
MFA_CHALLENGE_KEY = "mfa_challenge"
MFA_VERIFIED_KEY = "mfa_verified"


def generate_mfa_secret() -> str:
    """Generate a random base32 secret for TOTP."""
    return base64.b32encode(secrets.token_bytes(20)).decode("ascii")


def generate_mfa_uri(user_email: str, secret: str, issuer: str | None = None) -> str:
    """Generate a TOTP URI for QR code provisioning.

    Args:
        user_email: The user's email address.
        secret: The base32-encoded TOTP secret.
        issuer: The MFA issuer name (defaults to APP_NAME).
    """
    if issuer is None:
        issuer = settings.APP_NAME or "IdealEv.az"

    # OTPAuth URI format
    totp_uri = (
        f"otpauth://totp/{issuer}:{user_email}"
        f"?secret={secret}"
        f"&issuer={issuer}"
        "&algorithm=SHA1"
        "&period=30"
        "&digits=6"
    )
    return totp_uri


def verify_totp(secret: str, code: str) -> bool:
    """Verify a TOTP code against a secret.

    Uses passlib's time-based verification.
    """

    now = datetime.now(UTC)
    # Calculate the current time step
    time_step = int(now.timestamp()) // 30
    # Generate the expected hash for this time step
    # TOTP = HOTP(k, c) where c = floor(T / 30)
    # We use a simple approach: verify using the current and adjacent steps
    for step_offset in (-1, 0, 1):
        test_step = time_step + step_offset
        # Re-compute the hash
        key = base64.b32decode(secret, case="ignore")
        message = test_step.to_bytes(8, "big")
        import hashlib
        import hmac

        hmac_hash = hmac.new(key, message, hashlib.sha256).digest()
        # Dynamic truncation
        offset = hmac_hash[-1] & 0x0F
        binary = hmac_hash[offset : offset + 4]
        otp = (int.from_bytes(binary, "big") & 0x7FFFFFFF) % 1000000
        str_otp = str(otp).zfill(6)
        if str_otp == code:
            return True
    return False


def generate_backup_codes(count: int = 8) -> list[str]:
    """Generate a list of one-time backup codes for MFA recovery."""
    codes = []
    for _ in range(count):
        code = secrets.token_hex(4).upper()
        codes.append(code)
    return codes


def hash_backup_code(code: str) -> str:
    """Hash a backup code for secure storage."""
    return sha256_crypt.hash(code)


def verify_backup_code(code: str, hashed: str) -> bool:
    """Verify a backup code against its hash."""
    import bcrypt

    try:
        return bcrypt.checkpw(code.encode("utf-8"), hashed.encode("utf-8"))
    except (TypeError, ValueError):
        return False
