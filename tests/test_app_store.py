"""Smoke tests. Hit live endpoints — keep them off CI or behind a flag."""
from __future__ import annotations

import os

import pytest

from appstore_intel_mcp.providers.app_store import AppStoreProvider

pytestmark = pytest.mark.skipif(
    os.getenv("RUN_LIVE_TESTS") != "1",
    reason="Live network tests disabled. Set RUN_LIVE_TESTS=1 to enable.",
)


@pytest.mark.asyncio
async def test_app_store_search() -> None:
    provider = AppStoreProvider()
    results = await provider.search("calm meditation", country="us", limit=5)
    assert results
    assert any("calm" in r.title.lower() for r in results)


@pytest.mark.asyncio
async def test_app_store_metadata() -> None:
    provider = AppStoreProvider()
    meta = await provider.metadata("571800810", country="us")  # Calm
    assert meta.title
    assert meta.platform == "app_store"
