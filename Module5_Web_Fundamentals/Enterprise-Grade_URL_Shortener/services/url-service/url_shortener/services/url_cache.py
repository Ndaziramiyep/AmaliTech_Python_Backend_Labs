import json
from typing import Optional

from django.core.cache import cache

from url_shortener.domain.interfaces import UrlCacheBackend

CACHE_KEY_PREFIX = "url"


class RedisUrlCache(UrlCacheBackend):
    """Caches short_code -> {original_url, owner_id, owner_email} lookups via Django's configured cache backend."""

    def _key(self, short_code: str) -> str:
        return f"{CACHE_KEY_PREFIX}:{short_code}"

    def get(self, short_code: str) -> Optional[dict]:
        raw = cache.get(self._key(short_code))
        if raw is None:
            return None
        return json.loads(raw)

    def set(self, short_code: str, data: dict, timeout: int) -> None:
        cache.set(self._key(short_code), json.dumps(data), timeout=timeout)
