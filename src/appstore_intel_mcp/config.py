"""Runtime config loaded from environment variables."""
from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Auth
    api_keys: str = Field(
        default="",
        description="Comma-separated list of accepted bearer tokens. Empty disables auth (dev only).",
    )

    # Provider tuning
    request_timeout_s: float = 15.0
    user_agent: str = "appstore-intel-mcp/0.1 (+https://github.com/gautam84/appstore-intel-mcp)"

    # Cache
    cache_ttl_metadata_s: int = 60 * 60 * 6  # 6h
    cache_ttl_reviews_s: int = 60 * 30       # 30m
    cache_ttl_search_s: int = 60 * 60         # 1h

    # Limits — protect quotas in shared deployments
    max_reviews_per_call: int = 200
    max_search_results: int = 50

    def allowed_tokens(self) -> set[str]:
        return {t.strip() for t in self.api_keys.split(",") if t.strip()}


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
