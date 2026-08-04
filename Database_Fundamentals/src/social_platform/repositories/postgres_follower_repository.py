"""PostgreSQL-backed persistence for the follower graph, including the transactional follow."""

from __future__ import annotations

import psycopg2.errors

from social_platform.database.postgres_connection_pool import PostgresConnectionPool
from social_platform.models.exceptions import UserNotFoundError
from social_platform.models.results import FollowResult, UnfollowResult
from social_platform.repositories.interfaces import FollowerRepositoryInterface


class PostgresFollowerRepository(FollowerRepositoryInterface):
    """Implements `FollowerRepositoryInterface` against PostgreSQL via a connection pool."""

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
