"""The timeline feed use case: cached, paginated, and CTE-backed."""

from __future__ import annotations

from social_platform.features.feed.cache import TimelineCache
from social_platform.features.feed.model import FeedPostEntry
from social_platform.features.feed.repository import FeedRepository

_DEFAULT_PAGE_SIZE = 20


class FeedService:
    """Serves paginated timeline feed pages, checking the Redis cache before PostgreSQL."""

    def __init__(
        self,
        feed_repository: FeedRepository,
        timeline_cache: TimelineCache,
        page_size: int = _DEFAULT_PAGE_SIZE,
    ) -> None:
        self._feed_repository = feed_repository
        self._timeline_cache = timeline_cache
        self._page_size = page_size

    def get_user_feed_page(self, follower_user_id: int, page_number: int) -> list[FeedPostEntry]:
        """Return one 1-indexed page of `follower_user_id`'s timeline feed, newest first."""
        cached_feed_page = self._timeline_cache.get_cached_feed_page(follower_user_id, page_number)
        if cached_feed_page is not None:
            return cached_feed_page

        first_row = (page_number - 1) * self._page_size + 1
        last_row = page_number * self._page_size
        feed_page = self._feed_repository.fetch_feed_page(follower_user_id, first_row, last_row)
        self._timeline_cache.set_cached_feed_page(follower_user_id, page_number, feed_page)
        return feed_page
