"""PostgreSQL-backed persistence for user accounts."""

from __future__ import annotations

from typing import Any

import psycopg2.errors

from social_platform.database.postgres_connection_pool import PostgresConnectionPool
from social_platform.models.entities import User
from social_platform.models.exceptions import UserAlreadyExistsError
from social_platform.repositories.interfaces import UserRepositoryInterface


class PostgresUserRepository(UserRepositoryInterface):
    """Implements `UserRepositoryInterface` against PostgreSQL via a connection pool."""

    def __init__(self, connection_pool: PostgresConnectionPool) -> None:
        self._connection_pool = connection_pool

    def create_user(self, username: str, email: str, password_hash: str, display_name: str) -> User:
        """Insert a new user row and return the created entity."""
        try:
            with self._connection_pool.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO users (username, email, password_hash, display_name)
                    VALUES (%(username)s, %(email)s, %(password_hash)s, %(display_name)s)
                    RETURNING user_id, username, email, display_name, created_at
                    """,
                    {
                        "username": username,
                        "email": email,
                        "password_hash": password_hash,
                        "display_name": display_name,
                    },
                )
                row = cursor.fetchone()
        except psycopg2.errors.UniqueViolation as violation:
            raise UserAlreadyExistsError(
                f"A user with username {username!r} or email {email!r} already exists."
            ) from violation
        assert row is not None  # RETURNING always yields exactly one row on a successful insert
        return _row_to_user(row)

    def find_user_by_id(self, user_id: int) -> User | None:
        """Look up a user by id, returning None if no such user exists."""
        with self._connection_pool.cursor() as cursor:
            cursor.execute(
                """
                SELECT user_id, username, email, display_name, created_at
                FROM users
                WHERE user_id = %(user_id)s
                """,
                {"user_id": user_id},
            )
            row = cursor.fetchone()
        return _row_to_user(row) if row is not None else None

    def find_user_and_password_hash_by_username(self, username: str) -> tuple[User, str] | None:
        """Look up a user and their password hash by username, for authentication."""
        with self._connection_pool.cursor() as cursor:
            cursor.execute(
                """
                SELECT user_id, username, email, display_name, created_at, password_hash
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
        display_name=row["display_name"],
        created_at=row["created_at"],
    )
