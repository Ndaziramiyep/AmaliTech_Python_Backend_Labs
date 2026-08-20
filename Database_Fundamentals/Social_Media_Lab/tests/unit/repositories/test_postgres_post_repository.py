"""Unit tests for PostgresPostRepository: creating and looking up posts."""

from __future__ import annotations

from datetime import datetime
from unittest.mock import MagicMock

import psycopg2.errors
import pytest

from social_platform.common.exceptions import PostNotFoundError, UserNotFoundError
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
        "metadata": {"location": "Kigali"},
        "created_at": sample_created_at,
    }
    repository = PostgresPostRepository(fake_connection_pool)

    post = repository.create_post(1, "hello", {"location": "Kigali"})

    assert post.post_id == 1
    assert post.metadata == {"location": "Kigali"}


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


def test_find_posts_by_author_maps_every_row(
    fake_connection_pool: MagicMock, fake_cursor: MagicMock, sample_created_at: datetime
) -> None:
    """Each row from the author query becomes one Post."""
    fake_cursor.fetchall.return_value = [
        {
            "post_id": 1,
            "author_user_id": 1,
            "content": "hello",
            "metadata": {},
            "created_at": sample_created_at,
        }
    ]
    repository = PostgresPostRepository(fake_connection_pool)

    posts = repository.find_posts_by_author(1, 20)

    assert [post.post_id for post in posts] == [1]
    executed_params = fake_cursor.execute.call_args.args[1]
    assert executed_params == {"author_user_id": 1, "result_limit": 20}


def test_update_post_returns_the_updated_post(
    fake_connection_pool: MagicMock, fake_cursor: MagicMock, sample_created_at: datetime
) -> None:
    """A successful update returns the Post built from the RETURNING row."""
    fake_cursor.fetchone.return_value = {
        "post_id": 1,
        "author_user_id": 1,
        "content": "updated",
        "metadata": {},
        "created_at": sample_created_at,
    }
    repository = PostgresPostRepository(fake_connection_pool)

    post = repository.update_post(1, 1, "updated", {})

    assert post.content == "updated"


def test_update_post_raises_when_no_row_matches_post_id_and_author(
    fake_connection_pool: MagicMock, fake_cursor: MagicMock
) -> None:
    """A missing post-and-author combination (wrong owner or nonexistent) raises."""
    fake_cursor.fetchone.return_value = None
    repository = PostgresPostRepository(fake_connection_pool)

    with pytest.raises(PostNotFoundError):
        repository.update_post(1, 999, "hijacked", {})


def test_delete_post_raises_when_no_row_matches_post_id_and_author(
    fake_connection_pool: MagicMock, fake_cursor: MagicMock
) -> None:
    """A missing post-and-author combination (wrong owner or nonexistent) raises."""
    fake_cursor.rowcount = 0
    repository = PostgresPostRepository(fake_connection_pool)

    with pytest.raises(PostNotFoundError):
        repository.delete_post(1, 999)


def test_delete_post_succeeds_when_a_row_is_deleted(
    fake_connection_pool: MagicMock, fake_cursor: MagicMock
) -> None:
    """A matching post-and-author combination is deleted without raising."""
    fake_cursor.rowcount = 1
    repository = PostgresPostRepository(fake_connection_pool)

    repository.delete_post(1, 1)  # does not raise


def test_count_posts_by_author_returns_the_count(
    fake_connection_pool: MagicMock, fake_cursor: MagicMock
) -> None:
    """The count comes straight from the query's single row."""
    fake_cursor.fetchone.return_value = {"post_count": 3}
    repository = PostgresPostRepository(fake_connection_pool)

    assert repository.count_posts_by_author(1) == 3
