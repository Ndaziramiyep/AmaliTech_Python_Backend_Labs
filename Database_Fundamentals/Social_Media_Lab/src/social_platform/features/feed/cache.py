"""Timeline feed caching: the `TimelineCache` contract and its Redis implementation.

Uses a fixed time-to-live rather than write-time invalidation ("fan-out on read, short
TTL") -- creating a post does not proactively invalidate every follower's cached page,
which would not scale for high-follower-count accounts. Cached pages simply expire.
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Protocol

import redis

from social_platform.features.feed.model import FeedPostEntry


class TimelineCache(Protocol):
    """Cache contract for pre-rendered timeline feed pages. Services depend on this, not Redis."""

    def get_cached_feed_page(
        self, follower_user_id: int, page_number: int
    ) -> list[FeedPostEntry] | None:
        """Return a cached feed page, or None on a cache miss."""

    def set_cached_feed_page(
        self, follower_user_id: int, page_number: int, feed_page: list[FeedPostEntry]
    ) -> None:
        """Cache a feed page for the configured time-to-live."""


class RedisTimelineCache:
    """Implements `TimelineCache` against Redis with a fixed time-to-live."""

    def __init__(self, redis_client: redis.Redis, time_to_live_seconds: int) -> None:
        self._redis_client = redis_client
        self._time_to_live_seconds = time_to_live_seconds

    def get_cached_feed_page(
        self, follower_user_id: int, page_number: int
    ) -> list[FeedPostEntry] | None:
        """Return a cached feed page, or None on a cache miss."""
        cached_value = self._redis_client.get(_build_cache_key(follower_user_id, page_number))
        if cached_value is None:
            return None
        return [_entry_from_dict(entry) for entry in json.loads(cached_value)]

    def set_cached_feed_page(
        self, follower_user_id: int, page_number: int, feed_page: list[FeedPostEntry]
    ) -> None:
        """Cache a feed page for this cache's configured time-to-live."""
        self._redis_client.set(
            _build_cache_key(follower_user_id, page_number),
            json.dumps([_entry_to_dict(entry) for entry in feed_page]),
            ex=self._time_to_live_seconds,
        )


def _build_cache_key(follower_user_id: int, page_number: int) -> str:
    return f"timeline_feed:{follower_user_id}:{page_number}"


def _entry_to_dict(entry: FeedPostEntry) -> dict[str, Any]:
    return {
        "post_id": entry.post_id,
        "author_user_id": entry.author_user_id,
        "author_username": entry.author_username,
        "content": entry.content,
        "metadata": entry.metadata,
        "created_at": entry.created_at.isoformat(),
    }


def _entry_from_dict(entry: dict[str, Any]) -> FeedPostEntry:
    return FeedPostEntry(
        post_id=entry["post_id"],
        author_user_id=entry["author_user_id"],
        author_username=entry["author_username"],
        content=entry["content"],
        metadata=entry["metadata"],
        created_at=datetime.fromisoformat(entry["created_at"]),
    )
