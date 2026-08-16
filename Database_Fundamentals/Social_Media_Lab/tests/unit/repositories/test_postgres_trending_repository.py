"""Unit tests for PostgresTrendingRepository: posts ranked by recent comment count."""

from __future__ import annotations

from datetime import datetime
from unittest.mock import MagicMock

from social_platform.features.trending.repository import PostgresTrendingRepository


def test_fetch_trending_posts_maps_every_row(
    fake_connection_pool: MagicMock, fake_cursor: MagicMock, sample_created_at: datetime
) -> None:
    """Each row from the trending query becomes one TrendingPostEntry with its comment count."""
    fake_cursor.fetchall.return_value = [
        {
            "post_id": 1,
            "author_user_id": 2,
            "content": "hello",
            "metadata": {},
            "created_at": sample_created_at,
            "comment_count": 5,
        }
    ]
    repository = PostgresTrendingRepository(fake_connection_pool)

    trending_posts = repository.fetch_trending_posts(sample_created_at, 10)

    assert trending_posts[0].comment_count == 5
