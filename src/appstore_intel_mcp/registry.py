"""Provider registry."""
from __future__ import annotations

from functools import lru_cache

from .providers.app_store import AppStoreProvider
from .providers.base import StoreProvider
from .providers.google_play import GooglePlayProvider


@lru_cache(maxsize=1)
def _providers() -> dict[str, StoreProvider]:
    return {
        "google_play": GooglePlayProvider(),
        "app_store": AppStoreProvider(),
    }


def get_provider(platform: str) -> StoreProvider:
    providers = _providers()
    if platform not in providers:
        raise ValueError(
            f"Unknown platform '{platform}'. Use one of: {sorted(providers)}"
        )
    return providers[platform]
