"""Unit tests for TrendingService."""

from __future__ import annotations

from datetime import UTC, datetime

from social_platform.features.trending.service import TrendingService
from tests.unit.services._fakes import FakeTrendingRepository


def test_get_trending_posts_delegates_directly_to_the_repository(
    fake_trending_repository: FakeTrendingRepository,
) -> None:
    """The service is a thin pass-through to the repository's ranked query."""
    service = TrendingService(fake_trending_repository)
    since = datetime.now(UTC)

    result = service.get_trending_posts(since, 10)

    assert result is fake_trending_repository.trending_posts_to_return
