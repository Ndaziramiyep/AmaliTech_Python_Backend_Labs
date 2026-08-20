"""Unit tests for PostgresLikeRepository, including idempotent-like behavior."""

from __future__ import annotations

import types
from unittest.mock import MagicMock

import psycopg2.errors
import pytest

from social_platform.common.exceptions import PostNotFoundError, UserNotFoundError
from social_platform.features.likes.model import LikeResult, UnlikeResult
from social_platform.features.likes.repository import PostgresLikeRepository


class _ConstraintNamedViolation(psycopg2.errors.ForeignKeyViolation):
    """A ForeignKeyViolation whose `.diag.constraint_name` is fixed, for test purposes."""

    def __init__(self, constraint_name: str) -> None:
        super().__init__("boom")
        self._constraint_name = constraint_name

    @property
    def diag(self) -> types.SimpleNamespace:  # type: ignore[override]
        return types.SimpleNamespace(constraint_name=self._constraint_name)


def test_create_like_returns_created_when_a_row_is_inserted(
    fake_connection_pool: MagicMock, fake_cursor: MagicMock
) -> None:
    """A fresh like reports LikeResult.CREATED."""
    fake_cursor.rowcount = 1
    repository = PostgresLikeRepository(fake_connection_pool)

    assert repository.create_like(1, 2) is LikeResult.CREATED


def test_create_like_returns_already_exists_on_conflict(
    fake_connection_pool: MagicMock, fake_cursor: MagicMock
) -> None:
    """Liking the same post twice is idempotent: ON CONFLICT DO NOTHING inserts 0 rows."""
    fake_cursor.rowcount = 0
    repository = PostgresLikeRepository(fake_connection_pool)

    assert repository.create_like(1, 2) is LikeResult.ALREADY_EXISTS


def test_create_like_translates_missing_post_constraint_to_post_not_found(
    fake_connection_pool: MagicMock, fake_cursor: MagicMock
) -> None:
    """A violation of the post_id foreign key surfaces as a domain PostNotFoundError."""
    fake_cursor.execute.side_effect = _ConstraintNamedViolation("likes_post_id_fkey")
    repository = PostgresLikeRepository(fake_connection_pool)

    with pytest.raises(PostNotFoundError):
        repository.create_like(999, 2)


def test_create_like_translates_missing_user_constraint_to_user_not_found(
    fake_connection_pool: MagicMock, fake_cursor: MagicMock
) -> None:
    """A violation of the user_id foreign key surfaces as a domain UserNotFoundError."""
    fake_cursor.execute.side_effect = _ConstraintNamedViolation("likes_user_id_fkey")
    repository = PostgresLikeRepository(fake_connection_pool)

    with pytest.raises(UserNotFoundError):
        repository.create_like(1, 999)


def test_delete_like_returns_removed_when_a_row_is_deleted(
    fake_connection_pool: MagicMock, fake_cursor: MagicMock
) -> None:
    """Removing an actual like reports UnlikeResult.REMOVED."""
    fake_cursor.rowcount = 1
    repository = PostgresLikeRepository(fake_connection_pool)

    assert repository.delete_like(1, 2) is UnlikeResult.REMOVED


def test_delete_like_returns_did_not_exist_when_no_row_matches(
    fake_connection_pool: MagicMock, fake_cursor: MagicMock
) -> None:
    """Unliking a post not liked is idempotent, not an error."""
    fake_cursor.rowcount = 0
    repository = PostgresLikeRepository(fake_connection_pool)

    assert repository.delete_like(1, 2) is UnlikeResult.DID_NOT_EXIST


def test_has_user_liked_returns_true_when_a_row_matches(
    fake_connection_pool: MagicMock, fake_cursor: MagicMock
) -> None:
    """A matching like row reports True."""
    fake_cursor.fetchone.return_value = {"?column?": 1}
    repository = PostgresLikeRepository(fake_connection_pool)

    assert repository.has_user_liked(1, 2) is True


def test_has_user_liked_returns_false_when_no_row_matches(
    fake_connection_pool: MagicMock, fake_cursor: MagicMock
) -> None:
    """No matching like row reports False, not an error."""
    fake_cursor.fetchone.return_value = None
    repository = PostgresLikeRepository(fake_connection_pool)

    assert repository.has_user_liked(1, 2) is False
