from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.enums import UserRole


class ProfileRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    avatar_url: str | None = None
    bio: str | None = None
    city: str | None = Field(None, validation_alias="location")
    preferred_language: str = "az"
    member_since: date | None = None
    phone_verified: bool = False
    identity_verified: bool = False


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: EmailStr
    phone: str | None = None
    full_name: str
    role: UserRole
    is_active: bool
    is_verified: bool
    created_at: datetime
    profile: ProfileRead | None = None


class UserUpdate(BaseModel):
    full_name: str | None = Field(None, min_length=2, max_length=150)
    phone: str | None = Field(
        None, pattern=r"^\+994\d{9}$"
    )
    bio: str | None = Field(None, max_length=1000)
    city: str | None = Field(None, max_length=200)
    preferred_language: str | None = Field(None, pattern=r"^(az|ru|en)$")


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=2, max_length=150)
    phone: str | None = Field(None, pattern=r"^\+994\d{9}$")


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class AuthSuccess(BaseModel):
    user: UserRead
    detail: str = "ok"
