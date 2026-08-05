"""The trending-posts use case."""

from __future__ import annotations

from datetime import datetime

from social_platform.models.entities import TrendingPostEntry
from social_platform.repositories.interfaces import PostRepositoryInterface


class TrendingPostsService:
    """Returns posts ranked by recent comment count, via a single PostgreSQL CTE query."""

    def __init__(self, post_repository: PostRepositoryInterface) -> None:
        self._post_repository = post_repository

    def get_trending_posts(self, since: datetime, result_limit: int) -> list[TrendingPostEntry]:
        """Return posts created since `since`, most-commented first."""
        return self._post_repository.fetch_trending_posts(since, result_limit)
