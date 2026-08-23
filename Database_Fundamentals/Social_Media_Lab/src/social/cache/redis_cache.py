"""Redis-backed implementation of the Cache protocol."""
from typing import Optional

import redis


class RedisCache:
    """Cache protocol implementation backed by a real Redis connection."""

    def __init__(self, url: str) -> None:
        self._client = redis.Redis.from_url(url, decode_responses=True)

    def get(self, key: str) -> Optional[str]:
        """Return the cached value for `key`, or None on a miss."""
        return self._client.get(key)

    def set(self, key: str, value: str, ttl_seconds: int) -> None:
        """Cache `value` under `key`, expiring after `ttl_seconds`."""
        self._client.set(key, value, ex=ttl_seconds)

    def delete(self, key: str) -> None:
        """Evict `key`, if present."""
        self._client.delete(key)
