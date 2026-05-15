"""In-memory TTL cache.

Swap for Redis once you scale horizontally. The cache key includes the
tool name and arguments so tools never share entries by accident.
"""
from __future__ import annotations

import asyncio
import time
from typing import Any, Awaitable, Callable


class TTLCache:
    def __init__(self, max_size: int = 1024) -> None:
        self._store: dict[str, tuple[float, Any]] = {}
        self._max = max_size
        self._lock = asyncio.Lock()

    async def get_or_set(
        self,
        key: str,
        ttl_s: int,
        factory: Callable[[], Awaitable[Any]],
    ) -> Any:
        now = time.time()
        async with self._lock:
            hit = self._store.get(key)
            if hit and hit[0] > now:
                return hit[1]

        value = await factory()

        async with self._lock:
            if len(self._store) >= self._max:
                # Evict oldest entry; fine for low cardinality
                oldest = min(self._store.items(), key=lambda kv: kv[1][0])[0]
                self._store.pop(oldest, None)
            self._store[key] = (now + ttl_s, value)
        return value


cache = TTLCache()
