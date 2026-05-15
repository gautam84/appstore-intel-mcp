"""Apple App Store provider.

Search and basic metadata via the public iTunes Search API
(https://itunes.apple.com/search). Reviews via the RSS endpoint
(https://itunes.apple.com/{country}/rss/customerreviews/...). Both are
public and don't require auth.

TODO: For App Store Connect-only fields (install counts, conversion),
plug in App Store Connect API with JWT auth — out of scope for v0.1.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any

import httpx

from ..config import get_settings
from ..models import AppMetadata, AppSummary, Review, ReviewBatch


class AppStoreProvider:
    name = "app_store"

    def __init__(self) -> None:
        s = get_settings()
        self._client = httpx.AsyncClient(
            timeout=s.request_timeout_s,
            headers={"User-Agent": s.user_agent},
        )

    async def search(self, query: str, country: str, limit: int) -> list[AppSummary]:
        r = await self._client.get(
            "https://itunes.apple.com/search",
            params={
                "term": query,
                "country": country,
                "media": "software",
                "limit": limit,
            },
        )
        r.raise_for_status()
        data = r.json()
        return [
            AppSummary(
                platform="app_store",
                app_id=str(item["bundleId"]),
                title=item["trackName"],
                developer=item.get("artistName", ""),
                icon_url=item.get("artworkUrl512") or item.get("artworkUrl100"),
                rating=item.get("averageUserRating"),
                price=item.get("price") or 0.0,
                free=(item.get("price") or 0.0) == 0.0,
            )
            for item in data.get("results", [])
        ]

    async def metadata(self, app_id: str, country: str) -> AppMetadata:
        # iTunes lookup works by track ID or bundle ID
        params: dict[str, Any] = {"country": country}
        if app_id.isdigit():
            params["id"] = app_id
        else:
            params["bundleId"] = app_id
        r = await self._client.get("https://itunes.apple.com/lookup", params=params)
        r.raise_for_status()
        results = r.json().get("results", [])
        if not results:
            raise ValueError(f"App not found: {app_id}")
        item = results[0]
        return AppMetadata(
            platform="app_store",
            app_id=str(item.get("bundleId") or app_id),
            title=item["trackName"],
            developer=item.get("artistName", ""),
            developer_id=str(item.get("artistId") or "") or None,
            description=item.get("description", ""),
            category=item.get("primaryGenreName"),
            rating=item.get("averageUserRating"),
            rating_count=item.get("userRatingCount"),
            current_version=item.get("version"),
            last_updated=_parse_iso(item.get("currentVersionReleaseDate")),
            content_rating=item.get("contentAdvisoryRating"),
            website=item.get("sellerUrl"),
            screenshots=list(item.get("screenshotUrls") or []),
            languages=list(item.get("languageCodesISO2A") or []),
        )

    async def reviews(
        self,
        app_id: str,
        country: str,
        limit: int,
        sort: str,
        cursor: str | None,
    ) -> ReviewBatch:
        # App Store RSS feed: paginated, ~50 per page, max 10 pages
        page = int(cursor) if cursor else 1
        out: list[Review] = []
        while len(out) < limit and page <= 10:
            r = await self._client.get(
                f"https://itunes.apple.com/{country}/rss/customerreviews/"
                f"page={page}/id={app_id}/sortby=mostrecent/json"
            )
            if r.status_code != 200:
                break
            entries = r.json().get("feed", {}).get("entry", [])
            # First entry is the app itself when present
            for e in entries[1:] if entries and "im:rating" not in entries[0] else entries:
                if "im:rating" not in e:
                    continue
                out.append(
                    Review(
                        platform="app_store",
                        review_id=e["id"]["label"],
                        author=e.get("author", {}).get("name", {}).get("label"),
                        rating=int(e["im:rating"]["label"]),
                        title=e.get("title", {}).get("label"),
                        body=e.get("content", {}).get("label", ""),
                        app_version=e.get("im:version", {}).get("label"),
                    )
                )
                if len(out) >= limit:
                    break
            page += 1

        return ReviewBatch(
            platform="app_store",
            app_id=app_id,
            count=len(out),
            reviews=out,
            next_cursor=str(page) if page <= 10 else None,
        )


def _parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
