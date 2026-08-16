"""Unit tests for FeedService: cache-first, CTE-backed feed pagination."""

from __future__ import annotations

from social_platform.features.feed.service import FeedService
from tests.unit.services._fakes import FakeFeedRepository, FakeTimelineCache


def test_get_user_feed_page_returns_the_cached_page_without_querying_postgres(
    fake_feed_repository: FakeFeedRepository, fake_timeline_cache: FakeTimelineCache
) -> None:
    """A cache hit is returned as-is, with no call to the feed repository."""
    fake_timeline_cache.cached_pages[(1, 1)] = []
    service = FeedService(fake_feed_repository, fake_timeline_cache)

    service.get_user_feed_page(1, 1)

    assert fake_feed_repository.feed_page_calls == []


def test_get_user_feed_page_falls_back_to_postgres_on_a_cache_miss_and_populates_the_cache(
    fake_feed_repository: FakeFeedRepository, fake_timeline_cache: FakeTimelineCache
) -> None:
    """A cache miss queries PostgreSQL and populates the cache for next time."""
    service = FeedService(fake_feed_repository, fake_timeline_cache)

    service.get_user_feed_page(1, 1)

    assert fake_feed_repository.feed_page_calls == [(1, 1, 20)]
    assert (1, 1) in fake_timeline_cache.cached_pages


def test_get_user_feed_page_computes_row_bounds_from_the_page_number(
    fake_feed_repository: FakeFeedRepository, fake_timeline_cache: FakeTimelineCache
) -> None:
    """Page 3 with a page size of 20 requests rows 41 through 60."""
    service = FeedService(fake_feed_repository, fake_timeline_cache, page_size=20)

    service.get_user_feed_page(1, 3)

    assert fake_feed_repository.feed_page_calls == [(1, 41, 60)]
