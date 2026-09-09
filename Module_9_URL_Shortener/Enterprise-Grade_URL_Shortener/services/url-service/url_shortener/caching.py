import json

from django.conf import settings
from django.core.cache import cache

CACHE_KEY_PREFIX = "url"


def cache_key(short_code):
    """Builds the cache key used to store a short code's URL data."""
    return f"{CACHE_KEY_PREFIX}:{short_code}"


def identifiers_for(url_obj):
    """Returns every code (short_url, and custom_alias if set) that resolves to this Url."""
    codes = [url_obj.short_url]
    if url_obj.custom_alias:
        codes.append(url_obj.custom_alias)
    return codes


def cache_url(url_obj):
    """Caches a Url instance's data under every identifier that resolves to it."""
    data = {
        "original_url": url_obj.original_url,
        "owner_id": url_obj.owner_id,
        "owner_email": url_obj.owner_email,
        "is_active": url_obj.is_active,
        "expires_at": url_obj.expires_at.isoformat() if url_obj.expires_at else None,
    }
    encoded = json.dumps(data)
    for code in identifiers_for(url_obj):
        cache.set(cache_key(code), encoded, timeout=settings.URL_CACHE_TIMEOUT_SECONDS)
    return data


def invalidate_cache(url_obj):
    """Removes every identifier that resolves to this Url from the cache."""
    for code in identifiers_for(url_obj):
        cache.delete(cache_key(code))
