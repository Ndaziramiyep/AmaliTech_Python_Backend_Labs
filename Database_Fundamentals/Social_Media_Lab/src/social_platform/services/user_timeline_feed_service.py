"""The timeline feed use case: cached, paginated, and CTE-backed."""

from __future__ import annotations

from social_platform.models.entities import FeedPostEntry
from social_platform.repositories.interfaces import (
    PostRepositoryInterface,
    TimelineCacheRepositoryInterface,
)

_DEFAULT_PAGE_SIZE = 20


class UserTimelineFeedService:
    """Serves paginated timeline feed pages, checking the Redis cache before PostgreSQL."""

    def __init__(
        self,
        post_repository: PostRepositoryInterface,
        timeline_cache_repository: TimelineCacheRepositoryInterface,
        page_size: int = _DEFAULT_PAGE_SIZE,
    ) -> None:
        self._post_repository = post_repository
        self._timeline_cache_repository = timeline_cache_repository
        self._page_size = page_size

    def get_user_feed_page(self, follower_user_id: int, page_number: int) -> list[FeedPostEntry]:
        """Return one 1-indexed page of `follower_user_id`'s timeline feed, newest first."""
        cached_feed_page = self._timeline_cache_repository.get_cached_feed_page(
            follower_user_id, page_number
        )
        if cached_feed_page is not None:
            return cached_feed_page

        first_row = (page_number - 1) * self._page_size + 1
        last_row = page_number * self._page_size
        feed_page = self._post_repository.fetch_timeline_feed_page(
            follower_user_id, first_row, last_row
        )
        self._timeline_cache_repository.set_cached_feed_page(
            follower_user_id, page_number, feed_page
        )
        return feed_page
