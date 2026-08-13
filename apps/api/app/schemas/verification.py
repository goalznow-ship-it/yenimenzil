from __future__ import annotations

from pydantic import BaseModel, Field


class PasswordChangeRequest(BaseModel):
    current_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)


class ForgotPasswordRequest(BaseModel):
    email: str


class ResetPasswordRequest(BaseModel):
    token: str = Field(min_length=8, max_length=256)
    new_password: str = Field(min_length=8, max_length=128)


class VerifyTokenRequest(BaseModel):
    token: str = Field(min_length=8, max_length=256)


class VerificationStatusRead(BaseModel):
    email_verified: bool = False
    phone_verified: bool = False
    email_pending: bool = False
    phone_pending: bool = False
    verification_pending: bool = False
    verification_rejected: bool = False
    verification_reason: str | None = None


class NotificationPreferenceUpdate(BaseModel):
    email_enabled: bool | None = None
    push_enabled: bool | None = None


class NotificationPreferenceRead(BaseModel):
    email_enabled: bool
    push_enabled: bool
