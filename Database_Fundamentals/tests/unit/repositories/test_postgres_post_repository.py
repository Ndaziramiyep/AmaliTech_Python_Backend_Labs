"""Unit tests for PostgresPostRepository: post creation, feed paging, and trending posts."""

from __future__ import annotations

from datetime import datetime
from unittest.mock import MagicMock

import psycopg2.errors
import pytest

from social_platform.models.exceptions import UserNotFoundError
from social_platform.repositories.postgres_post_repository import PostgresPostRepository


def test_create_post_translates_foreign_key_violation(
    fake_connection_pool: MagicMock, fake_cursor: MagicMock
) -> None:
    """A nonexistent author surfaces as a domain UserNotFoundError, not psycopg2's."""
    fake_cursor.execute.side_effect = psycopg2.errors.ForeignKeyViolation("boom")
    repository = PostgresPostRepository(fake_connection_pool)

    with pytest.raises(UserNotFoundError):
        repository.create_post(999, "hello", {})


def test_create_post_returns_the_row_returned_by_the_insert(
    fake_connection_pool: MagicMock, fake_cursor: MagicMock, sample_created_at: datetime
) -> None:
    """The repository builds a Post entity from the RETURNING row, including JSONB metadata."""
    fake_cursor.fetchone.return_value = {
        "post_id": 1,
        "author_user_id": 1,
        "content": "hello",
        "metadata": {"tags": ["python"]},
        "created_at": sample_created_at,
    }
    repository = PostgresPostRepository(fake_connection_pool)

    post = repository.create_post(1, "hello", {"tags": ["python"]})

    assert post.post_id == 1
    assert post.metadata == {"tags": ["python"]}


def test_fetch_timeline_feed_page_maps_every_row_and_passes_pagination_bounds(
    fake_connection_pool: MagicMock, fake_cursor: MagicMock, sample_created_at: datetime
) -> None:
    """Each row from the feed query becomes one FeedPostEntry, and bounds are parameterized."""
    fake_cursor.fetchall.return_value = [
        {
            "post_id": 1,
            "author_user_id": 2,
            "author_username": "ada",
            "content": "hello",
            "metadata": {},
            "created_at": sample_created_at,
        }
    ]
    repository = PostgresPostRepository(fake_connection_pool)

    feed_page = repository.fetch_timeline_feed_page(1, 1, 20)

    assert len(feed_page) == 1
    assert feed_page[0].author_username == "ada"
    executed_params = fake_cursor.execute.call_args.args[1]
    assert executed_params == {"follower_user_id": 1, "first_row": 1, "last_row": 20}


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
    repository = PostgresPostRepository(fake_connection_pool)

    trending_posts = repository.fetch_trending_posts(sample_created_at, 10)

    assert trending_posts[0].comment_count == 5
