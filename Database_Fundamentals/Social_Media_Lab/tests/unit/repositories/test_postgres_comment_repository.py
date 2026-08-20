"""Unit tests for PostgresCommentRepository, including foreign-key-violation translation."""

from __future__ import annotations

import types
from datetime import datetime
from unittest.mock import MagicMock

import psycopg2.errors
import pytest

from social_platform.common.exceptions import (
    CommentNotFoundError,
    PostNotFoundError,
    UserNotFoundError,
)
from social_platform.features.comments.repository import PostgresCommentRepository


class _ConstraintNamedViolation(psycopg2.errors.ForeignKeyViolation):
    """A ForeignKeyViolation whose `.diag.constraint_name` is fixed, for test purposes.

    Real psycopg2 errors expose `.diag` as a non-writable, C-level attribute backed by the
    driver's diagnostic info, so it cannot be set directly on an instance. Overriding it with
    a property on a subclass is the only way to fake it for a unit test.
    """

    def __init__(self, constraint_name: str) -> None:
        super().__init__("boom")
        self._constraint_name = constraint_name

    @property
    def diag(self) -> types.SimpleNamespace:  # type: ignore[override]
        return types.SimpleNamespace(constraint_name=self._constraint_name)


def _make_violation(constraint_name: str) -> psycopg2.errors.ForeignKeyViolation:
    """Build a ForeignKeyViolation whose `.diag.constraint_name` is set, for test purposes."""
    return _ConstraintNamedViolation(constraint_name)


def test_create_comment_returns_the_row_returned_by_the_insert(
    fake_connection_pool: MagicMock, fake_cursor: MagicMock, sample_created_at: datetime
) -> None:
    """The repository builds a Comment entity from the RETURNING row."""
    fake_cursor.fetchone.return_value = {
        "comment_id": 1,
        "post_id": 10,
        "commenter_user_id": 2,
        "parent_comment_id": None,
        "content": "nice post",
        "created_at": sample_created_at,
    }
    repository = PostgresCommentRepository(fake_connection_pool)

    comment = repository.create_comment(10, 2, "nice post")

    assert comment.comment_id == 1
    assert comment.content == "nice post"


def test_create_comment_translates_missing_post_constraint_to_post_not_found(
    fake_connection_pool: MagicMock, fake_cursor: MagicMock
) -> None:
    """A violation of the post_id foreign key surfaces as a domain PostNotFoundError."""
    fake_cursor.execute.side_effect = _make_violation("comments_post_id_fkey")
    repository = PostgresCommentRepository(fake_connection_pool)

    with pytest.raises(PostNotFoundError):
        repository.create_comment(999, 2, "nice post")


def test_create_comment_translates_missing_commenter_constraint_to_user_not_found(
    fake_connection_pool: MagicMock, fake_cursor: MagicMock
) -> None:
    """A violation of the commenter_user_id foreign key surfaces as a domain UserNotFoundError."""
    fake_cursor.execute.side_effect = _make_violation("comments_commenter_user_id_fkey")
    repository = PostgresCommentRepository(fake_connection_pool)

    with pytest.raises(UserNotFoundError):
        repository.create_comment(10, 999, "nice post")


def test_create_comment_translates_missing_parent_constraint_to_comment_not_found(
    fake_connection_pool: MagicMock, fake_cursor: MagicMock
) -> None:
    """A violation of the parent_comment_id foreign key surfaces as CommentNotFoundError."""
    fake_cursor.execute.side_effect = _make_violation("comments_parent_comment_id_fkey")
    repository = PostgresCommentRepository(fake_connection_pool)

    with pytest.raises(CommentNotFoundError):
        repository.create_comment(10, 2, "nice reply", parent_comment_id=999)


def test_find_comment_thread_for_post_builds_entries_with_depth(
    fake_connection_pool: MagicMock, fake_cursor: MagicMock, sample_created_at: datetime
) -> None:
    """Each row from the recursive query becomes a CommentThreadEntry carrying its depth."""
    fake_cursor.fetchall.return_value = [
        {
            "comment_id": 1,
            "post_id": 10,
            "commenter_user_id": 2,
            "parent_comment_id": None,
            "content": "top-level comment",
            "created_at": sample_created_at,
            "depth": 0,
        },
        {
            "comment_id": 2,
            "post_id": 10,
            "commenter_user_id": 3,
            "parent_comment_id": 1,
            "content": "a reply",
            "created_at": sample_created_at,
            "depth": 1,
        },
    ]
    repository = PostgresCommentRepository(fake_connection_pool)

    thread = repository.find_comment_thread_for_post(10)

    assert [entry.depth for entry in thread] == [0, 1]
    assert thread[1].comment.parent_comment_id == 1


def test_find_comment_by_id_returns_none_when_no_row_matches(
    fake_connection_pool: MagicMock, fake_cursor: MagicMock
) -> None:
    """A missing comment id is reported as None, not as an exception."""
    fake_cursor.fetchone.return_value = None
    repository = PostgresCommentRepository(fake_connection_pool)

    assert repository.find_comment_by_id(999) is None


def test_find_comment_by_id_returns_the_matching_comment(
    fake_connection_pool: MagicMock, fake_cursor: MagicMock, sample_created_at: datetime
) -> None:
    """A matching comment id returns the Comment built from that row."""
    fake_cursor.fetchone.return_value = {
        "comment_id": 1,
        "post_id": 10,
        "commenter_user_id": 2,
        "parent_comment_id": None,
        "content": "nice post",
        "created_at": sample_created_at,
    }
    repository = PostgresCommentRepository(fake_connection_pool)

    comment = repository.find_comment_by_id(1)

    assert comment is not None
    assert comment.comment_id == 1


def test_delete_comment_raises_when_no_row_matches_comment_id_and_commenter(
    fake_connection_pool: MagicMock, fake_cursor: MagicMock
) -> None:
    """A missing comment-and-commenter combination (wrong owner or nonexistent) raises."""
    fake_cursor.rowcount = 0
    repository = PostgresCommentRepository(fake_connection_pool)

    with pytest.raises(CommentNotFoundError):
        repository.delete_comment(1, 999)


def test_delete_comment_succeeds_when_a_row_is_deleted(
    fake_connection_pool: MagicMock, fake_cursor: MagicMock
) -> None:
    """A matching comment-and-commenter combination is deleted without raising."""
    fake_cursor.rowcount = 1
    repository = PostgresCommentRepository(fake_connection_pool)

    repository.delete_comment(1, 2)  # does not raise
