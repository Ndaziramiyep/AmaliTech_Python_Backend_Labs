"""Protocol for the timeline cache that services depend on instead of importing redis directly."""
from __future__ import annotations

from typing import Optional, Protocol


class Cache(Protocol):
    """Protocol for a key-value cache with expiring entries."""

    def get(self, key: str) -> Optional[str]:
        """Return the cached value for a key, or None if absent."""
        ...

    def set(self, key: str, value: str, ttl_seconds: int) -> None:
        """Store a value under a key with a time-to-live in seconds."""
        ...

    def delete(self, key: str) -> None:
        """Remove a key from the cache."""
        ...
