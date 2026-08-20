"""Unit tests for PostgresUserRepository."""

from __future__ import annotations

from datetime import datetime
from unittest.mock import MagicMock

from social_platform.features.users.model import User
from social_platform.features.users.repository import PostgresUserRepository


def test_create_user_returns_the_row_returned_by_the_insert(
    fake_connection_pool: MagicMock, fake_cursor: MagicMock, sample_created_at: datetime
) -> None:
    """The repository builds a User entity from the RETURNING row, not from the inputs."""
    fake_cursor.fetchone.return_value = {
        "user_id": 1,
        "username": "ada",
        "email": "ada@example.com",
        "bio": "Mathematician.",
        "created_at": sample_created_at,
    }
    repository = PostgresUserRepository(fake_connection_pool)

    user = repository.create_user("ada", "ada@example.com", "hashed-password", "Mathematician.")

    assert user == User(1, "ada", "ada@example.com", "Mathematician.", sample_created_at)
    executed_sql, executed_params = fake_cursor.execute.call_args.args
    assert "INSERT INTO users" in executed_sql
    assert executed_params["password_hash"] == "hashed-password"
    assert executed_params["bio"] == "Mathematician."


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
        "bio": None,
        "created_at": sample_created_at,
        "password_hash": "deadbeef:cafef00d",
    }
    repository = PostgresUserRepository(fake_connection_pool)

    result = repository.find_user_and_password_hash_by_username("grace")

    assert result is not None
    user, password_hash = result
    assert user == User(42, "grace", "grace@example.com", None, sample_created_at)
    assert password_hash == "deadbeef:cafef00d"
    executed_sql, executed_params = fake_cursor.execute.call_args.args
    assert executed_params == {"username": "grace"}
    assert "%(username)s" in executed_sql


def test_find_user_by_username_returns_none_when_no_row_matches(
    fake_connection_pool: MagicMock, fake_cursor: MagicMock
) -> None:
    """A username with no matching account is reported as None, not as an exception."""
    fake_cursor.fetchone.return_value = None
    repository = PostgresUserRepository(fake_connection_pool)

    assert repository.find_user_by_username("nobody") is None


def test_update_bio_returns_the_updated_user(
    fake_connection_pool: MagicMock, fake_cursor: MagicMock, sample_created_at: datetime
) -> None:
    """A successful bio update returns the User built from the RETURNING row."""
    fake_cursor.fetchone.return_value = {
        "user_id": 1,
        "username": "ada",
        "email": "ada@example.com",
        "bio": "New bio.",
        "created_at": sample_created_at,
    }
    repository = PostgresUserRepository(fake_connection_pool)

    user = repository.update_bio(1, "New bio.")

    assert user.bio == "New bio."
    executed_sql, executed_params = fake_cursor.execute.call_args.args
    assert "UPDATE users" in executed_sql
    assert executed_params == {"user_id": 1, "bio": "New bio."}


def test_search_users_by_username_maps_every_row(
    fake_connection_pool: MagicMock, fake_cursor: MagicMock, sample_created_at: datetime
) -> None:
    """Each matching row becomes one User, and the query is wildcard-wrapped."""
    fake_cursor.fetchall.return_value = [
        {
            "user_id": 1,
            "username": "ada",
            "email": "ada@example.com",
            "bio": None,
            "created_at": sample_created_at,
        }
    ]
    repository = PostgresUserRepository(fake_connection_pool)

    users = repository.search_users_by_username("ad", 10)

    assert [user.username for user in users] == ["ada"]
    executed_sql, executed_params = fake_cursor.execute.call_args.args
    assert "ILIKE" in executed_sql
    assert executed_params == {"pattern": "%ad%", "result_limit": 10}
