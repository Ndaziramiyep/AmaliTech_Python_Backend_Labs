"""Unit tests for RedisTimelineCache, backed by an in-memory fakeredis client."""

from __future__ import annotations

from datetime import datetime

import fakeredis

from social_platform.features.feed.cache import RedisTimelineCache
from social_platform.features.feed.model import FeedPostEntry


def _make_cache(time_to_live_seconds: int = 60) -> RedisTimelineCache:
    fake_redis_client = fakeredis.FakeRedis(decode_responses=True)
    return RedisTimelineCache(fake_redis_client, time_to_live_seconds)


def test_get_cached_feed_page_returns_none_on_a_cache_miss() -> None:
    """An unpopulated cache key reports a miss instead of raising."""
    cache = _make_cache()

    assert cache.get_cached_feed_page(1, 1) is None


def test_set_then_get_cached_feed_page_round_trips_every_field(
    sample_created_at: datetime,
) -> None:
    """A cached feed page is returned with every field intact, including the timestamp."""
    cache = _make_cache()
    feed_page = [
        FeedPostEntry(
            post_id=1,
            author_user_id=2,
            author_username="ada",
            content="hello",
            metadata={"tags": ["python"]},
            created_at=sample_created_at,
        )
    ]

    cache.set_cached_feed_page(1, 1, feed_page)

    assert cache.get_cached_feed_page(1, 1) == feed_page


def test_cached_feed_pages_for_different_users_do_not_collide(
    sample_created_at: datetime,
) -> None:
    """Cache keys are scoped per follower and per page."""
    cache = _make_cache()
    feed_page = [FeedPostEntry(1, 2, "ada", "hello", {}, sample_created_at)]

    cache.set_cached_feed_page(1, 1, feed_page)

    assert cache.get_cached_feed_page(2, 1) is None
