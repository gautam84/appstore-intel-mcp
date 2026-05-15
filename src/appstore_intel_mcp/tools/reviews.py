"""get_reviews — pull recent reviews for an app."""
from __future__ import annotations

from typing import Literal

from mcp.server.fastmcp import FastMCP

from ..cache import cache
from ..config import get_settings
from ..models import ReviewBatch
from ..registry import get_provider


def register(mcp: FastMCP) -> None:
    s = get_settings()

    @mcp.tool()
    async def get_reviews(
        app_id: str,
        platform: str = "google_play",
        country: str = "us",
        limit: int = 50,
        sort: Literal["newest", "rating", "helpful"] = "newest",
        cursor: str | None = None,
    ) -> ReviewBatch:
        """Fetch reviews for an app.

        Args:
            app_id: Package name (Android) or bundle ID / track ID (iOS)
            platform: "google_play" or "app_store"
            country: Storefront country code
            limit: Number of reviews (max 200)
            sort: "newest", "rating", or "helpful"
            cursor: Pagination cursor from a previous call's `next_cursor`
        """
        limit = max(1, min(limit, s.max_reviews_per_call))
        key = f"reviews:{platform}:{country}:{app_id}:{sort}:{limit}:{cursor or ''}"

        async def _do():
            return await get_provider(platform).reviews(
                app_id, country, limit, sort, cursor
            )

        return await cache.get_or_set(key, s.cache_ttl_reviews_s, _do)
