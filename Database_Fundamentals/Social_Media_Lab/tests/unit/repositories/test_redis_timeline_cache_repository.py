"""Unit tests for RedisTimelineCacheRepository, backed by an in-memory fakeredis client."""

from __future__ import annotations

from datetime import datetime

import fakeredis

from social_platform.models.entities import FeedPostEntry
from social_platform.repositories.redis_timeline_cache_repository import (
    RedisTimelineCacheRepository,
)


def _make_repository(time_to_live_seconds: int = 60) -> RedisTimelineCacheRepository:
    fake_redis_client = fakeredis.FakeRedis(decode_responses=True)
    return RedisTimelineCacheRepository(fake_redis_client, time_to_live_seconds)


def test_get_cached_feed_page_returns_none_on_a_cache_miss() -> None:
    """An unpopulated cache key reports a miss instead of raising."""
    repository = _make_repository()

    assert repository.get_cached_feed_page(1, 1) is None


def test_set_then_get_cached_feed_page_round_trips_every_field(
    sample_created_at: datetime,
) -> None:
    """A cached feed page is returned with every field intact, including the timestamp."""
    repository = _make_repository()
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

    repository.set_cached_feed_page(1, 1, feed_page)

    assert repository.get_cached_feed_page(1, 1) == feed_page


def test_cached_feed_pages_for_different_users_do_not_collide(
    sample_created_at: datetime,
) -> None:
    """Cache keys are scoped per follower and per page."""
    repository = _make_repository()
    feed_page = [FeedPostEntry(1, 2, "ada", "hello", {}, sample_created_at)]

    repository.set_cached_feed_page(1, 1, feed_page)

    assert repository.get_cached_feed_page(2, 1) is None
