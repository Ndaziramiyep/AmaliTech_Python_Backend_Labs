"""User persistence: the `UserRepository` contract and its PostgreSQL implementation."""

from __future__ import annotations

from typing import Any, Protocol

import psycopg2.errors

from social_platform.common.exceptions import UserAlreadyExistsError, UserNotFoundError
from social_platform.common.postgres_pool import PostgresConnectionPool
from social_platform.features.users.model import User


class UserRepository(Protocol):
    """Persistence contract for user accounts. Services depend on this, not on Postgres."""

    def create_user(self, username: str, email: str, password_hash: str, bio: str | None) -> User:
        """Persist a new user and return the created entity."""

    def find_user_and_password_hash_by_username(self, username: str) -> tuple[User, str] | None:
        """Return the user and their password hash for a username, or None if no match."""

    def find_user_by_username(self, username: str) -> User | None:
        """Return the user with the given username, or None if no such user exists."""

    def update_bio(self, user_id: int, bio: str | None) -> User:
        """Replace a user's bio and return the updated entity."""

    def search_users_by_username(self, query: str, result_limit: int) -> list[User]:
        """Return users whose username contains `query` (case-insensitive), alphabetically."""


class PostgresUserRepository:
    """Implements `UserRepository` against PostgreSQL via a pooled connection."""

    def __init__(self, connection_pool: PostgresConnectionPool) -> None:
        self._connection_pool = connection_pool

    def create_user(self, username: str, email: str, password_hash: str, bio: str | None) -> User:
        """Insert a new user row and return the created entity."""
        try:
            with self._connection_pool.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO users (username, email, password_hash, bio)
                    VALUES (%(username)s, %(email)s, %(password_hash)s, %(bio)s)
                    RETURNING user_id, username, email, bio, created_at
                    """,
                    {
                        "username": username,
                        "email": email,
                        "password_hash": password_hash,
                        "bio": bio,
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
                SELECT user_id, username, email, bio, created_at, password_hash
                FROM users
                WHERE username = %(username)s
                """,
                {"username": username},
            )
            row = cursor.fetchone()
        return (_row_to_user(row), row["password_hash"]) if row is not None else None

    def find_user_by_username(self, username: str) -> User | None:
        """Look up a user by username, returning None if no such user exists."""
        with self._connection_pool.cursor() as cursor:
            cursor.execute(
                """
                SELECT user_id, username, email, bio, created_at
                FROM users
                WHERE username = %(username)s
                """,
                {"username": username},
            )
            row = cursor.fetchone()
        return _row_to_user(row) if row is not None else None

    def update_bio(self, user_id: int, bio: str | None) -> User:
        """Replace a user's bio in one transaction and return the updated entity."""
        with self._connection_pool.cursor() as cursor:
            cursor.execute(
                """
                UPDATE users
                SET bio = %(bio)s
                WHERE user_id = %(user_id)s
                RETURNING user_id, username, email, bio, created_at
                """,
                {"user_id": user_id, "bio": bio},
            )
            row = cursor.fetchone()
        if row is None:
            raise UserNotFoundError(f"No user with id {user_id!r} exists.")
        return _row_to_user(row)

    def search_users_by_username(self, query: str, result_limit: int) -> list[User]:
        """Return users whose username contains `query` (case-insensitive), alphabetically."""
        with self._connection_pool.cursor() as cursor:
            cursor.execute(
                """
                SELECT user_id, username, email, bio, created_at
                FROM users
                WHERE username ILIKE %(pattern)s
                ORDER BY username
                LIMIT %(result_limit)s
                """,
                {"pattern": f"%{query}%", "result_limit": result_limit},
            )
            rows = cursor.fetchall()
        return [_row_to_user(row) for row in rows]


def _row_to_user(row: dict[str, Any]) -> User:
    return User(
        user_id=row["user_id"],
        username=row["username"],
        email=row["email"],
        bio=row["bio"],
        created_at=row["created_at"],
    )
