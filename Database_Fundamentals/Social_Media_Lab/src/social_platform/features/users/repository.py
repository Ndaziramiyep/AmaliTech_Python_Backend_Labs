"""User persistence: the `UserRepository` contract and its PostgreSQL implementation."""

from __future__ import annotations

from typing import Any, Protocol

import psycopg2.errors

from social_platform.common.exceptions import UserAlreadyExistsError
from social_platform.common.postgres_pool import PostgresConnectionPool
from social_platform.features.users.model import User


class UserRepository(Protocol):
    """Persistence contract for user accounts. Services depend on this, not on Postgres."""

    def create_user(self, username: str, email: str, password_hash: str) -> User:
        """Persist a new user and return the created entity."""

    def find_user_and_password_hash_by_username(self, username: str) -> tuple[User, str] | None:
        """Return the user and their password hash for a username, or None if no match."""


class PostgresUserRepository:
    """Implements `UserRepository` against PostgreSQL via a pooled connection."""

    def __init__(self, connection_pool: PostgresConnectionPool) -> None:
        self._connection_pool = connection_pool

    def create_user(self, username: str, email: str, password_hash: str) -> User:
        """Insert a new user row and return the created entity."""
        try:
            with self._connection_pool.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO users (username, email, password_hash)
                    VALUES (%(username)s, %(email)s, %(password_hash)s)
                    RETURNING user_id, username, email, created_at
                    """,
                    {
                        "username": username,
                        "email": email,
                        "password_hash": password_hash,
                    },
                )
                row = cursor.fetchone()
        except psycopg2.errors.UniqueViolation as violation:
            raise UserAlreadyExistsError(
                f"A user with username {username!r} or email {email!r} already exists."
            ) from violation
        assert row is not None  # RETURNING always yields exactly one row on a successful insert
        return _row_to_user(row)

    def find_user_and_password_hash_by_username(self, username: str) -> tuple[User, str] | None:
        """Look up a user and their password hash by username, for authentication."""
        with self._connection_pool.cursor() as cursor:
            cursor.execute(
                """
                SELECT user_id, username, email, created_at, password_hash
                FROM users
                WHERE username = %(username)s
                """,
                {"username": username},
            )
            row = cursor.fetchone()
        return (_row_to_user(row), row["password_hash"]) if row is not None else None


def _row_to_user(row: dict[str, Any]) -> User:
    return User(
        user_id=row["user_id"],
        username=row["username"],
        email=row["email"],
        created_at=row["created_at"],
    )
