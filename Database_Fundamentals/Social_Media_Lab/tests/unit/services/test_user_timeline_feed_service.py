"""Unit tests for UserTimelineFeedService: cache-first, CTE-backed feed pagination."""

from __future__ import annotations

from social_platform.services.user_timeline_feed_service import UserTimelineFeedService
from tests.unit.services._fakes import FakePostRepository, FakeTimelineCacheRepository


def test_get_user_feed_page_returns_the_cached_page_without_querying_postgres(
    fake_post_repository: FakePostRepository,
    fake_timeline_cache_repository: FakeTimelineCacheRepository,
) -> None:
    """A cache hit is returned as-is, with no call to the post repository."""
    fake_timeline_cache_repository.cached_pages[(1, 1)] = []
    service = UserTimelineFeedService(fake_post_repository, fake_timeline_cache_repository)

    service.get_user_feed_page(1, 1)

    assert fake_post_repository.feed_page_calls == []


def test_get_user_feed_page_falls_back_to_postgres_on_a_cache_miss_and_populates_the_cache(
    fake_post_repository: FakePostRepository,
    fake_timeline_cache_repository: FakeTimelineCacheRepository,
) -> None:
    """A cache miss queries PostgreSQL and populates the cache for next time."""
    service = UserTimelineFeedService(fake_post_repository, fake_timeline_cache_repository)

    service.get_user_feed_page(1, 1)

    assert fake_post_repository.feed_page_calls == [(1, 1, 20)]
    assert (1, 1) in fake_timeline_cache_repository.cached_pages


def test_get_user_feed_page_computes_row_bounds_from_the_page_number(
    fake_post_repository: FakePostRepository,
    fake_timeline_cache_repository: FakeTimelineCacheRepository,
) -> None:
    """Page 3 with a page size of 20 requests rows 41 through 60."""
    service = UserTimelineFeedService(
        fake_post_repository, fake_timeline_cache_repository, page_size=20
    )

    service.get_user_feed_page(1, 3)

    assert fake_post_repository.feed_page_calls == [(1, 41, 60)]
