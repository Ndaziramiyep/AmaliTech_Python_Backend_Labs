"""Unit tests for PostgresCommentRepository, including foreign-key-violation translation."""

from __future__ import annotations

import types
from datetime import datetime
from unittest.mock import MagicMock

import psycopg2.errors
import pytest

from social_platform.models.exceptions import PostNotFoundError, UserNotFoundError
from social_platform.repositories.postgres_comment_repository import (
    PostgresCommentRepository,
)


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
