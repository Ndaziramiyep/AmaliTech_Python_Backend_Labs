"""Unit tests for PostgresUserRepository."""

from __future__ import annotations

from datetime import datetime
from unittest.mock import MagicMock

from social_platform.models.entities import User
from social_platform.repositories.postgres_user_repository import PostgresUserRepository


def test_create_user_returns_the_row_returned_by_the_insert(
    fake_connection_pool: MagicMock, fake_cursor: MagicMock, sample_created_at: datetime
) -> None:
    """The repository builds a User entity from the RETURNING row, not from the inputs."""
    fake_cursor.fetchone.return_value = {
        "user_id": 1,
        "username": "ada",
        "email": "ada@example.com",
        "display_name": "Ada Lovelace",
        "created_at": sample_created_at,
    }
    repository = PostgresUserRepository(fake_connection_pool)

    user = repository.create_user("ada", "ada@example.com", "hashed-password", "Ada Lovelace")

    assert user == User(1, "ada", "ada@example.com", "Ada Lovelace", sample_created_at)
    executed_sql, executed_params = fake_cursor.execute.call_args.args
    assert "INSERT INTO users" in executed_sql
    assert executed_params["password_hash"] == "hashed-password"


def test_find_user_by_id_returns_none_when_no_row_matches(
    fake_connection_pool: MagicMock, fake_cursor: MagicMock
) -> None:
    """A missing user id is reported as None, not as an exception."""
    fake_cursor.fetchone.return_value = None
    repository = PostgresUserRepository(fake_connection_pool)

    assert repository.find_user_by_id(999) is None


def test_find_user_by_id_queries_by_the_given_id(
    fake_connection_pool: MagicMock, fake_cursor: MagicMock, sample_created_at: datetime
) -> None:
    """The lookup is parameterized on `user_id`, never string-interpolated."""
    fake_cursor.fetchone.return_value = {
        "user_id": 42,
        "username": "grace",
        "email": "grace@example.com",
        "display_name": "Grace Hopper",
        "created_at": sample_created_at,
    }
    repository = PostgresUserRepository(fake_connection_pool)

    user = repository.find_user_by_id(42)

    assert user is not None
    assert user.user_id == 42
    executed_sql, executed_params = fake_cursor.execute.call_args.args
    assert executed_params == {"user_id": 42}
    assert "%(user_id)s" in executed_sql


def test_find_user_and_password_hash_by_username_returns_none_when_no_row_matches(
    fake_connection_pool: MagicMock, fake_cursor: MagicMock
) -> None:
    """A username with no matching account is reported as None, not as an exception."""
    fake_cursor.fetchone.return_value = None
    repository = PostgresUserRepository(fake_connection_pool)

    assert repository.find_user_and_password_hash_by_username("nobody") is None


def test_find_user_and_password_hash_by_username_returns_the_user_and_hash(
    fake_connection_pool: MagicMock, fake_cursor: MagicMock, sample_created_at: datetime
) -> None:
    """The lookup is parameterized on `username` and returns both the user and its hash."""
    fake_cursor.fetchone.return_value = {
        "user_id": 42,
        "username": "grace",
        "email": "grace@example.com",
        "display_name": "Grace Hopper",
        "created_at": sample_created_at,
        "password_hash": "deadbeef:cafef00d",
    }
    repository = PostgresUserRepository(fake_connection_pool)

    result = repository.find_user_and_password_hash_by_username("grace")

    assert result is not None
    user, password_hash = result
    assert user == User(42, "grace", "grace@example.com", "Grace Hopper", sample_created_at)
    assert password_hash == "deadbeef:cafef00d"
    executed_sql, executed_params = fake_cursor.execute.call_args.args
    assert executed_params == {"username": "grace"}
    assert "%(username)s" in executed_sql
