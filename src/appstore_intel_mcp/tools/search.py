"""search_apps — find an app's identifier from a free-text query."""
from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from ..cache import cache
from ..config import get_settings
from ..models import AppSummary
from ..registry import get_provider


def register(mcp: FastMCP) -> None:
    s = get_settings()

    @mcp.tool()
    async def search_apps(
        query: str,
        platform: str = "google_play",
        country: str = "us",
        limit: int = 10,
    ) -> list[AppSummary]:
        """Search Google Play or the App Store.

        Args:
            query: Free-text search ("meditation", "calm app", etc.)
            platform: "google_play" or "app_store"
            country: Two-letter store country code (default "us")
            limit: 1..50 results
        """
        limit = max(1, min(limit, s.max_search_results))
        key = f"search:{platform}:{country}:{query.lower()}:{limit}"

        async def _do():
            return await get_provider(platform).search(query, country, limit)

        return await cache.get_or_set(key, s.cache_ttl_search_s, _do)
