"""Advertising schemas (Phase 15)."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import ClassVar

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models.ad_campaign import AdCampaign


class AdPlacement(str):
    LEFT_RAIL = "LEFT_RAIL"
    RIGHT_RAIL = "RIGHT_RAIL"
    HOME_TOP_BANNER = "HOME_TOP_BANNER"
    HOME_MIDDLE_BANNER = "HOME_MIDDLE_BANNER"
    SEARCH_TOP_BANNER = "SEARCH_TOP_BANNER"
    SEARCH_INLINE_BANNER = "SEARCH_INLINE_BANNER"
    SEARCH_BOTTOM_BANNER = "SEARCH_BOTTOM_BANNER"
    PROPERTY_SIDE_AD = "PROPERTY_SIDE_AD"
    PROPERTY_INLINE_AD = "PROPERTY_INLINE_AD"
    MOBILE_TOP = "MOBILE_TOP"
    MOBILE_INLINE = "MOBILE_INLINE"
    MOBILE_BOTTOM = "MOBILE_BOTTOM"

    _placements: ClassVar[list] = [
        LEFT_RAIL,
        RIGHT_RAIL,
        HOME_TOP_BANNER,
        HOME_MIDDLE_BANNER,
        SEARCH_TOP_BANNER,
        SEARCH_INLINE_BANNER,
        SEARCH_BOTTOM_BANNER,
        PROPERTY_SIDE_AD,
        PROPERTY_INLINE_AD,
        MOBILE_TOP,
        MOBILE_INLINE,
        MOBILE_BOTTOM,
    ]

    @classmethod
    def all(cls) -> list[str]:
        return cls._placements


PLACEMENT_DIMS = {
    "LEFT_RAIL": (300, 600),
    "RIGHT_RAIL": (300, 600),
    "HOME_TOP_BANNER": (970, 250),
    "HOME_MIDDLE_BANNER": (970, 180),
    "SEARCH_TOP_BANNER": (970, 180),
    "SEARCH_INLINE_BANNER": (970, 180),
    "SEARCH_BOTTOM_BANNER": (970, 180),
    "PROPERTY_SIDE_AD": (300, 600),
    "PROPERTY_INLINE_AD": (970, 180),
    "MOBILE_TOP": (320, 50),
    "MOBILE_INLINE": (320, 100),
    "MOBILE_BOTTOM": (320, 100),
}

DEVICE_TARGETING = ("all", "desktop", "mobile")


class AdCampaignBase(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    advertiser: str = Field(min_length=2, max_length=200)
    placement: str = Field(pattern="|".join(AdPlacement._placements))
    desktop_creative_url: str | None = Field(None, max_length=1000)
    mobile_creative_url: str | None = Field(None, max_length=1000)
    alt_text: str | None = Field(None, max_length=300)
    destination_url: str = Field(min_length=1, max_length=1000)
    open_in_new_tab: bool = True
    start_at: datetime | None = None
    end_at: datetime | None = None
    device_targeting: str = Field(default="all", pattern="|".join(DEVICE_TARGETING))
    city_targeting: list[str] = Field(default_factory=list)
    property_category_targeting: list[str] = Field(default_factory=list)
    priority: int = Field(default=0, ge=0, le=100)
    enabled: bool = True

    @model_validator(mode="after")
    def _at_least_one_creative(self):
        if self.desktop_creative_url is None and self.mobile_creative_url is None:
            raise ValueError(
                "At least one of desktop_creative_url or mobile_creative_url must be provided"
            )
        return self


class AdCampaignCreate(AdCampaignBase):
    pass


class AdCampaignUpdate(BaseModel):
    name: str | None = Field(None, min_length=2, max_length=200)
    advertiser: str | None = Field(None, min_length=2, max_length=200)
    placement: str | None = Field(None, pattern="|".join(AdPlacement._placements))
    desktop_creative_url: str | None = Field(None, max_length=1000)
    mobile_creative_url: str | None = Field(None, max_length=1000)
    alt_text: str | None = Field(None, max_length=300)
    destination_url: str | None = Field(None, max_length=1000)
    open_in_new_tab: bool | None = None
    start_at: datetime | None = None
    end_at: datetime | None = None
    device_targeting: str | None = Field(None, pattern="|".join(DEVICE_TARGETING))
    city_targeting: list[str] | None = None
    property_category_targeting: list[str] | None = None
    priority: int | None = Field(None, ge=0, le=100)
    enabled: bool | None = None
    archived: bool | None = None


class AdCampaignRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    advertiser: str
    placement: str
    desktop_creative_url: str | None
    mobile_creative_url: str | None
    alt_text: str | None
    destination_url: str
    open_in_new_tab: bool
    start_at: datetime | None
    end_at: datetime | None
    device_targeting: str
    city_targeting: list[str]
    property_category_targeting: list[str]
    priority: int
    enabled: bool
    archived: bool
    impressions: int
    clicks: int
    ctr: float
    state: str
    created_by: uuid.UUID | None
    created_at: datetime
    updated_at: datetime

    @field_validator("state", mode="before")
    @classmethod
    def _compute_state(cls, v, info):
        if isinstance(info.data, AdCampaign):
            return info.data.state
        return v


class AdCampaignPublic(BaseModel):
    """Minimal public response for ad rendering."""

    id: uuid.UUID
    placement: str
    desktop_creative_url: str | None
    mobile_creative_url: str | None
    alt_text: str | None
    destination_url: str
    open_in_new_tab: bool


class AdImpressionRequest(BaseModel):
    session_key: str | None = None


class AdClickRequest(BaseModel):
    session_key: str | None = None


class AdDailyStatsRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    date: datetime
    impressions: int
    clicks: int
    unique_impressions: int
    unique_clicks: int
    ctr: float
