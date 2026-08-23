"""Protocol for the timeline cache. Services depend only on this, never on
redis directly.
"""
from __future__ import annotations

from typing import Optional, Protocol


class Cache(Protocol):
    def get(self, key: str) -> Optional[str]: ...

    def set(self, key: str, value: str, ttl_seconds: int) -> None: ...

    def delete(self, key: str) -> None: ...
