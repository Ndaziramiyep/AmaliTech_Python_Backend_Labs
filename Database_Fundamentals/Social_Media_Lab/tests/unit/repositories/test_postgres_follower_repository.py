"""Unit tests for PostgresFollowerRepository, including the transactional follow contract."""

from __future__ import annotations

from unittest.mock import MagicMock

import psycopg2.errors
import pytest

from social_platform.common.exceptions import UserNotFoundError
from social_platform.features.followers.model import FollowResult, UnfollowResult
from social_platform.features.followers.repository import PostgresFollowerRepository


def test_create_follow_relationship_returns_created_when_a_row_is_inserted(
    fake_connection_pool: MagicMock, fake_cursor: MagicMock
) -> None:
    """A fresh follow edge reports FollowResult.CREATED."""
    fake_cursor.rowcount = 1
    repository = PostgresFollowerRepository(fake_connection_pool)

    assert repository.create_follow_relationship(1, 2) is FollowResult.CREATED


def test_create_follow_relationship_returns_already_exists_on_conflict(
    fake_connection_pool: MagicMock, fake_cursor: MagicMock
) -> None:
    """Re-following the same user is idempotent: ON CONFLICT DO NOTHING inserts 0 rows."""
    fake_cursor.rowcount = 0
    repository = PostgresFollowerRepository(fake_connection_pool)

    assert repository.create_follow_relationship(1, 2) is FollowResult.ALREADY_EXISTS


def test_create_follow_relationship_translates_foreign_key_violation(
    fake_connection_pool: MagicMock, fake_cursor: MagicMock
) -> None:
    """A nonexistent follower or followee surfaces as a domain UserNotFoundError, not psycopg2's."""
    fake_cursor.execute.side_effect = psycopg2.errors.ForeignKeyViolation("boom")
    repository = PostgresFollowerRepository(fake_connection_pool)

    with pytest.raises(UserNotFoundError):
        repository.create_follow_relationship(1, 999)


def test_delete_follow_relationship_returns_removed_when_a_row_is_deleted(
    fake_connection_pool: MagicMock, fake_cursor: MagicMock
) -> None:
    """Unfollowing an actually-followed user reports UnfollowResult.REMOVED."""
    fake_cursor.rowcount = 1
    repository = PostgresFollowerRepository(fake_connection_pool)

    assert repository.delete_follow_relationship(1, 2) is UnfollowResult.REMOVED


def test_delete_follow_relationship_returns_did_not_exist_when_no_row_matches(
    fake_connection_pool: MagicMock, fake_cursor: MagicMock
) -> None:
    """Unfollowing a user not followed is idempotent, not an error."""
    fake_cursor.rowcount = 0
    repository = PostgresFollowerRepository(fake_connection_pool)

    assert repository.delete_follow_relationship(1, 2) is UnfollowResult.DID_NOT_EXIST


def test_count_followers_returns_the_count(
    fake_connection_pool: MagicMock, fake_cursor: MagicMock
) -> None:
    """The follower count comes straight from the query's single row."""
    fake_cursor.fetchone.return_value = {"follower_count": 4}
    repository = PostgresFollowerRepository(fake_connection_pool)

    assert repository.count_followers(1) == 4


def test_count_following_returns_the_count(
    fake_connection_pool: MagicMock, fake_cursor: MagicMock
) -> None:
    """The following count comes straight from the query's single row."""
    fake_cursor.fetchone.return_value = {"following_count": 7}
    repository = PostgresFollowerRepository(fake_connection_pool)

    assert repository.count_following(1) == 7


def test_is_following_returns_true_when_a_row_matches(
    fake_connection_pool: MagicMock, fake_cursor: MagicMock
) -> None:
    """A matching follow-edge row reports True."""
    fake_cursor.fetchone.return_value = {"?column?": 1}
    repository = PostgresFollowerRepository(fake_connection_pool)

    assert repository.is_following(1, 2) is True


def test_is_following_returns_false_when_no_row_matches(
    fake_connection_pool: MagicMock, fake_cursor: MagicMock
) -> None:
    """No matching follow-edge row reports False, not an error."""
    fake_cursor.fetchone.return_value = None
    repository = PostgresFollowerRepository(fake_connection_pool)

    assert repository.is_following(1, 2) is False
