"""PostgreSQL-backed persistence for comments."""

from __future__ import annotations

from typing import Any

import psycopg2.errors

from social_platform.database.postgres_connection_pool import PostgresConnectionPool
from social_platform.models.entities import Comment
from social_platform.models.exceptions import PostNotFoundError, UserNotFoundError
from social_platform.repositories.interfaces import CommentRepositoryInterface


class PostgresCommentRepository(CommentRepositoryInterface):
    """Implements `CommentRepositoryInterface` against PostgreSQL via a connection pool."""

    def __init__(self, connection_pool: PostgresConnectionPool) -> None:
        self._connection_pool = connection_pool

    def create_comment(self, post_id: int, commenter_user_id: int, content: str) -> Comment:
        """Insert a new comment row and return the created entity."""
        try:
            with self._connection_pool.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO comments (post_id, commenter_user_id, content)
                    VALUES (%(post_id)s, %(commenter_user_id)s, %(content)s)
                    RETURNING comment_id, post_id, commenter_user_id, content, created_at
                    """,
                    {
                        "post_id": post_id,
                        "commenter_user_id": commenter_user_id,
                        "content": content,
                    },
                )
                row = cursor.fetchone()
        except psycopg2.errors.ForeignKeyViolation as violation:
            constraint_name = violation.diag.constraint_name or ""
            if "post_id" in constraint_name:
                raise PostNotFoundError(f"No post with id {post_id!r} exists.") from violation
            raise UserNotFoundError(f"No user with id {commenter_user_id!r} exists.") from violation
        assert row is not None  # RETURNING always yields exactly one row on a successful insert
        return _row_to_comment(row)


def _row_to_comment(row: dict[str, Any]) -> Comment:
    return Comment(
        comment_id=row["comment_id"],
        post_id=row["post_id"],
        commenter_user_id=row["commenter_user_id"],
        content=row["content"],
        created_at=row["created_at"],
    )
