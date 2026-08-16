"""Unit tests for PostgresPostRepository: creating and looking up posts."""

from __future__ import annotations

from datetime import datetime
from unittest.mock import MagicMock

import psycopg2.errors
import pytest

from social_platform.common.exceptions import UserNotFoundError
from social_platform.features.posts.repository import PostgresPostRepository


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


def test_find_post_by_id_returns_none_when_no_row_matches(
    fake_connection_pool: MagicMock, fake_cursor: MagicMock
) -> None:
    """A missing post id is reported as None, not as an exception."""
    fake_cursor.fetchone.return_value = None
    repository = PostgresPostRepository(fake_connection_pool)

    assert repository.find_post_by_id(999) is None


def test_find_post_by_id_returns_the_matching_post(
    fake_connection_pool: MagicMock, fake_cursor: MagicMock, sample_created_at: datetime
) -> None:
    """A matching post id returns the Post built from that row."""
    fake_cursor.fetchone.return_value = {
        "post_id": 1,
        "author_user_id": 2,
        "content": "hello",
        "metadata": {},
        "created_at": sample_created_at,
    }
    repository = PostgresPostRepository(fake_connection_pool)

    post = repository.find_post_by_id(1)

    assert post is not None
    assert post.post_id == 1
