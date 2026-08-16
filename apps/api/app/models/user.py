from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    String,
    Text,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import UserRole

if TYPE_CHECKING:
    from app.models.agency import Agent
    from app.models.analytics import AnalyticsEvent
    from app.models.appointment import ViewingAppointment
    from app.models.auth import RefreshToken
    from app.models.favorite import Favorite, FavoriteCollection
    from app.models.messaging import Conversation, Message
    from app.models.notification import Notification
    from app.models.property import Property
    from app.models.saved_search import SavedSearch
    from app.models.verification import NotificationPreference, VerificationToken
    from app.models.wallet import Wallet


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    phone: Mapped[str | None] = mapped_column(String(32), unique=True, nullable=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str] = mapped_column(String(150))
    role: Mapped[UserRole] = mapped_column(
        String(32), default=UserRole.USER.value, nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    profile: Mapped[Profile] = relationship(
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    properties: Mapped[list[Property]] = relationship(back_populates="owner")
    favorites: Mapped[list[Favorite]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    favorite_collections: Mapped[list[FavoriteCollection]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    refresh_tokens: Mapped[list[RefreshToken]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    saved_searches: Mapped[list[SavedSearch]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    analytics_events: Mapped[list[AnalyticsEvent]] = relationship(back_populates="user")
    notifications: Mapped[list[Notification]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    agent_records: Mapped[list[Agent]] = relationship(
        foreign_keys="Agent.user_id", lazy="selectin"
    )
    wallet: Mapped[Wallet | None] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    verification_tokens: Mapped[list[VerificationToken]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    notification_preferences: Mapped[list[NotificationPreference]] = relationship(
        cascade="all, delete-orphan"
    )
    conversations_as_buyer: Mapped[list[Conversation]] = relationship(
        foreign_keys="Conversation.buyer_id",
        back_populates="buyer",
        cascade="all, delete-orphan",
    )
    conversations_as_seller: Mapped[list[Conversation]] = relationship(
        foreign_keys="Conversation.seller_id",
        back_populates="seller",
        cascade="all, delete-orphan",
    )
    sent_messages: Mapped[list[Message]] = relationship(
        back_populates="sender", cascade="all, delete-orphan"
    )
    viewing_requests: Mapped[list[ViewingAppointment]] = relationship(
        foreign_keys="ViewingAppointment.requester_id",
        back_populates="requester",
        cascade="all, delete-orphan",
    )
    viewing_hosting: Mapped[list[ViewingAppointment]] = relationship(
        foreign_keys="ViewingAppointment.owner_id",
        back_populates="owner",
        cascade="all, delete-orphan",
    )


class Profile(Base):
    __tablename__ = "profiles"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True
    )
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    location: Mapped[str | None] = mapped_column(String(200), nullable=True)
    preferred_language: Mapped[str] = mapped_column(
        String(8), default="az", nullable=False
    )
    member_since: Mapped[date | None] = mapped_column(Date, nullable=True)
    phone_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    identity_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user: Mapped[User] = relationship(back_populates="profile")
