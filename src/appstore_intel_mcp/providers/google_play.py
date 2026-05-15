"""Google Play provider.

Implementation uses the `google-play-scraper` package which scrapes the
public Play Store web pages. No API key required, but rate-limit yourself
and cache aggressively in production.
"""
from __future__ import annotations

import asyncio
from datetime import datetime

from ..models import AppMetadata, AppSummary, Review, ReviewBatch


class GooglePlayProvider:
    name = "google_play"

    async def search(self, query: str, country: str, limit: int) -> list[AppSummary]:
        from google_play_scraper import search as gp_search  # lazy import

        def _do() -> list[dict]:
            return gp_search(query, country=country, n_hits=limit)

        rows = await asyncio.to_thread(_do)
        return [
            AppSummary(
                platform="google_play",
                app_id=r["appId"],
                title=r["title"],
                developer=r.get("developer", ""),
                icon_url=r.get("icon"),
                rating=r.get("score"),
                price=r.get("price") or 0.0,
                free=bool(r.get("free", True)),
            )
            for r in rows
        ]

    async def metadata(self, app_id: str, country: str) -> AppMetadata:
        from google_play_scraper import app as gp_app

        def _do() -> dict:
            return gp_app(app_id, country=country)

        r = await asyncio.to_thread(_do)
        return AppMetadata(
            platform="google_play",
            app_id=app_id,
            title=r["title"],
            developer=r.get("developer", ""),
            developer_id=str(r.get("developerId") or "") or None,
            description=r.get("description", ""),
            short_description=r.get("summary"),
            category=r.get("genre"),
            rating=r.get("score"),
            rating_count=r.get("ratings"),
            install_count_band=r.get("installs"),
            current_version=r.get("version"),
            last_updated=(
                datetime.fromtimestamp(r["updated"]) if r.get("updated") else None
            ),
            content_rating=r.get("contentRating"),
            in_app_purchases=bool(r.get("offersIAP")),
            contains_ads=bool(r.get("adSupported")),
            privacy_policy_url=r.get("privacyPolicy"),
            website=r.get("developerWebsite"),
            screenshots=list(r.get("screenshots") or []),
        )

    async def reviews(
        self,
        app_id: str,
        country: str,
        limit: int,
        sort: str,
        cursor: str | None,
    ) -> ReviewBatch:
        from google_play_scraper import Sort, reviews as gp_reviews

        sort_map = {
            "newest": Sort.NEWEST,
            "rating": Sort.RATING,
            "helpful": Sort.MOST_RELEVANT,
        }

        def _do() -> tuple[list[dict], str | None]:
            return gp_reviews(
                app_id,
                country=country,
                count=limit,
                sort=sort_map.get(sort, Sort.NEWEST),
                continuation_token=cursor,
            )

        rows, next_cursor = await asyncio.to_thread(_do)
        reviews_out = [
            Review(
                platform="google_play",
                review_id=row["reviewId"],
                author=row.get("userName"),
                rating=row["score"],
                body=row.get("content", ""),
                created_at=row.get("at"),
                app_version=row.get("reviewCreatedVersion"),
                helpful_count=row.get("thumbsUpCount"),
                developer_reply=row.get("replyContent"),
                developer_reply_at=row.get("repliedAt"),
            )
            for row in rows
        ]
        return ReviewBatch(
            platform="google_play",
            app_id=app_id,
            count=len(reviews_out),
            reviews=reviews_out,
            next_cursor=next_cursor,
        )
