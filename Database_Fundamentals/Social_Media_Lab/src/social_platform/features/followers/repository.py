"""Follower-graph persistence: the `FollowerRepository` contract and its transactional
PostgreSQL implementation.
"""

from __future__ import annotations

from typing import Protocol

import psycopg2.errors

from social_platform.common.exceptions import UserNotFoundError
from social_platform.common.postgres_pool import PostgresConnectionPool
from social_platform.features.followers.model import FollowResult, UnfollowResult


class FollowerRepository(Protocol):
    """Persistence contract for the follower graph. Services depend on this, not on Postgres."""

    def create_follow_relationship(
        self, follower_user_id: int, followee_user_id: int
    ) -> FollowResult:
        """Create a follow edge, or report that it already existed."""

    def delete_follow_relationship(
        self, follower_user_id: int, followee_user_id: int
    ) -> UnfollowResult:
        """Remove a follow edge, or report that it did not exist."""


class PostgresFollowerRepository:
    """Implements `FollowerRepository` against PostgreSQL via a pooled connection.

    Each method runs as one atomic transaction (see `PostgresConnectionPool.cursor`):
    it commits on a clean exit and rolls back on any exception. Neither this class nor
    its caller ever touches a raw connection or calls commit/rollback directly.
    """

    def __init__(self, connection_pool: PostgresConnectionPool) -> None:
        self._connection_pool = connection_pool

    def create_follow_relationship(
        self, follower_user_id: int, followee_user_id: int
    ) -> FollowResult:
        """Insert a follow edge in one transaction; a duplicate edge is a no-op, not an error."""
        try:
            with self._connection_pool.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO followers (follower_user_id, followee_user_id)
                    VALUES (%(follower_user_id)s, %(followee_user_id)s)
                    ON CONFLICT (follower_user_id, followee_user_id) DO NOTHING
                    """,
                    {
                        "follower_user_id": follower_user_id,
                        "followee_user_id": followee_user_id,
                    },
                )
                rows_inserted = cursor.rowcount
        except psycopg2.errors.ForeignKeyViolation as violation:
            raise UserNotFoundError(
                "Both the follower and the followee must be existing users."
            ) from violation
        return FollowResult.CREATED if rows_inserted else FollowResult.ALREADY_EXISTS

    def delete_follow_relationship(
        self, follower_user_id: int, followee_user_id: int
    ) -> UnfollowResult:
        """Remove a follow edge in one transaction; a missing edge is a no-op, not an error."""
        with self._connection_pool.cursor() as cursor:
            cursor.execute(
                """
                DELETE FROM followers
                WHERE follower_user_id = %(follower_user_id)s
                  AND followee_user_id = %(followee_user_id)s
                """,
                {"follower_user_id": follower_user_id, "followee_user_id": followee_user_id},
            )
            rows_deleted = cursor.rowcount
        return UnfollowResult.REMOVED if rows_deleted else UnfollowResult.DID_NOT_EXIST
