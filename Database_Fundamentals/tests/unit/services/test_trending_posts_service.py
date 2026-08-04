"""Unit tests for TrendingPostsService."""

from __future__ import annotations

from datetime import UTC, datetime

from social_platform.services.trending_posts_service import TrendingPostsService
from tests.unit.services._fakes import FakePostRepository


def test_get_trending_posts_delegates_directly_to_the_repository(
    fake_post_repository: FakePostRepository,
) -> None:
    """The service is a thin pass-through to the repository's ranked query."""
    service = TrendingPostsService(fake_post_repository)
    since = datetime.now(UTC)

    result = service.get_trending_posts(since, 10)

    assert result is fake_post_repository.trending_posts_to_return
