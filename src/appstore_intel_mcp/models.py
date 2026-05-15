"""Shared response models. Stable schemas across Play and App Store."""
from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

Platform = Literal["google_play", "app_store"]


class AppSummary(BaseModel):
    """Lightweight result for search."""
    platform: Platform
    app_id: str = Field(description="Bundle ID (iOS) or package name (Android)")
    title: str
    developer: str
    icon_url: str | None = None
    rating: float | None = None
    price: float | None = None
    free: bool = True


class AppMetadata(BaseModel):
    platform: Platform
    app_id: str
    title: str
    developer: str
    developer_id: str | None = None
    description: str
    short_description: str | None = None
    category: str | None = None
    rating: float | None = None
    rating_count: int | None = None
    install_count_band: str | None = None  # e.g. "1,000,000+"
    current_version: str | None = None
    last_updated: datetime | None = None
    content_rating: str | None = None
    in_app_purchases: bool | None = None
    contains_ads: bool | None = None
    privacy_policy_url: str | None = None
    website: str | None = None
    screenshots: list[str] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=list)
    countries: list[str] = Field(default_factory=list)


class Review(BaseModel):
    platform: Platform
    review_id: str
    author: str | None = None
    rating: int
    title: str | None = None
    body: str
    created_at: datetime | None = None
    app_version: str | None = None
    helpful_count: int | None = None
    developer_reply: str | None = None
    developer_reply_at: datetime | None = None


class ReviewBatch(BaseModel):
    platform: Platform
    app_id: str
    count: int
    reviews: list[Review]
    next_cursor: str | None = None
