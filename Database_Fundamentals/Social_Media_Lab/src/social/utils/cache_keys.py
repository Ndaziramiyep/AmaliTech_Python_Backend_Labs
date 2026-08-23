"""Cache key convention shared by writers (follow_service, invalidating) and
readers (feed_service, cache-aside) of the Redis-backed timeline cache."""


def timeline_cache_key(user_id: int) -> str:
    return f"timeline:{user_id}"
