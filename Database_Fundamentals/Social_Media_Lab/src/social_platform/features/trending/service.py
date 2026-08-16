"""The trending-posts use case."""

from __future__ import annotations

from datetime import datetime

from social_platform.features.trending.model import TrendingPostEntry
from social_platform.features.trending.repository import TrendingRepository


class TrendingService:
    """Returns posts ranked by recent comment count, via a single PostgreSQL CTE query."""

    def __init__(self, trending_repository: TrendingRepository) -> None:
        self._trending_repository = trending_repository

    def get_trending_posts(self, since: datetime, result_limit: int) -> list[TrendingPostEntry]:
        """Return posts created since `since`, most-commented first."""
        return self._trending_repository.fetch_trending_posts(since, result_limit)
