"""Provider protocol. Each store backend implements this interface."""
from __future__ import annotations

from typing import Protocol

from ..models import AppMetadata, AppSummary, ReviewBatch


class StoreProvider(Protocol):
    name: str

    async def search(self, query: str, country: str, limit: int) -> list[AppSummary]: ...

    async def metadata(self, app_id: str, country: str) -> AppMetadata: ...

    async def reviews(
        self,
        app_id: str,
        country: str,
        limit: int,
        sort: str,
        cursor: str | None,
    ) -> ReviewBatch: ...
