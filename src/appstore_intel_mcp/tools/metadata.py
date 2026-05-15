"""get_app_metadata — full listing details for one app."""
from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from ..cache import cache
from ..config import get_settings
from ..models import AppMetadata
from ..registry import get_provider


def register(mcp: FastMCP) -> None:
    s = get_settings()

    @mcp.tool()
    async def get_app_metadata(
        app_id: str,
        platform: str = "google_play",
        country: str = "us",
    ) -> AppMetadata:
        """Fetch full metadata for a single app.

        Args:
            app_id: Package name (Android, e.g. "com.calm.android")
                or bundle ID / iTunes track ID (iOS)
            platform: "google_play" or "app_store"
            country: Storefront country code (default "us")
        """
        key = f"meta:{platform}:{country}:{app_id}"

        async def _do():
            return await get_provider(platform).metadata(app_id, country)

        return await cache.get_or_set(key, s.cache_ttl_metadata_s, _do)
