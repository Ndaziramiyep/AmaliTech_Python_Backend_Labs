"""Like persistence: the `LikeRepository` contract and its PostgreSQL implementation."""

from __future__ import annotations

from typing import Protocol

import psycopg2.errors

from social_platform.common.exceptions import PostNotFoundError, UserNotFoundError
from social_platform.common.postgres_pool import PostgresConnectionPool
from social_platform.features.likes.model import LikeResult, UnlikeResult


class LikeRepository(Protocol):
    """Persistence contract for likes. Services depend on this, not on Postgres."""

    def create_like(self, post_id: int, user_id: int) -> LikeResult:
        """Create a like, or report that it already existed."""

    def delete_like(self, post_id: int, user_id: int) -> UnlikeResult:
        """Remove a like, or report that it did not exist."""

    def has_user_liked(self, post_id: int, user_id: int) -> bool:
        """Return whether `user_id` currently has a like recorded on `post_id`."""


class PostgresLikeRepository:
    """Implements `LikeRepository` against PostgreSQL via a pooled connection.

    Liking the same post twice is idempotent -- `INSERT ... ON CONFLICT DO NOTHING`,
    the same pattern `PostgresFollowerRepository` uses for follow/unfollow -- rather
    than raising a unique-violation on the second attempt.
    """

    def __init__(self, connection_pool: PostgresConnectionPool) -> None:
        self._connection_pool = connection_pool

    def create_like(self, post_id: int, user_id: int) -> LikeResult:
        """Insert a like in one transaction; a duplicate like is a no-op, not an error."""
        try:
            with self._connection_pool.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO likes (post_id, user_id)
                    VALUES (%(post_id)s, %(user_id)s)
                    ON CONFLICT (post_id, user_id) DO NOTHING
                    """,
                    {"post_id": post_id, "user_id": user_id},
                )
                rows_inserted = cursor.rowcount
        except psycopg2.errors.ForeignKeyViolation as violation:
            constraint_name = violation.diag.constraint_name or ""
            if "post_id" in constraint_name:
                raise PostNotFoundError(f"No post with id {post_id!r} exists.") from violation
            raise UserNotFoundError(f"No user with id {user_id!r} exists.") from violation
        return LikeResult.CREATED if rows_inserted else LikeResult.ALREADY_EXISTS

    def delete_like(self, post_id: int, user_id: int) -> UnlikeResult:
        """Remove a like in one transaction; a missing like is a no-op, not an error."""
        with self._connection_pool.cursor() as cursor:
            cursor.execute(
                """
                DELETE FROM likes
                WHERE post_id = %(post_id)s AND user_id = %(user_id)s
                """,
                {"post_id": post_id, "user_id": user_id},
            )
            rows_deleted = cursor.rowcount
        return UnlikeResult.REMOVED if rows_deleted else UnlikeResult.DID_NOT_EXIST

    def has_user_liked(self, post_id: int, user_id: int) -> bool:
        """Return whether `user_id` currently has a like recorded on `post_id`."""
        with self._connection_pool.cursor() as cursor:
            cursor.execute(
                """
                SELECT 1 FROM likes
                WHERE post_id = %(post_id)s AND user_id = %(user_id)s
                """,
                {"post_id": post_id, "user_id": user_id},
            )
            row = cursor.fetchone()
        return row is not None
