"""Comment persistence: the `CommentRepository` contract and its PostgreSQL implementation."""

from __future__ import annotations

from typing import Any, Protocol

import psycopg2.errors

from social_platform.common.exceptions import (
    CommentNotFoundError,
    PostNotFoundError,
    UserNotFoundError,
)
from social_platform.common.postgres_pool import PostgresConnectionPool
from social_platform.features.comments.model import Comment, CommentThreadEntry


class CommentRepository(Protocol):
    """Persistence contract for comments. Services depend on this, not on Postgres."""

    def create_comment(
        self,
        post_id: int,
        commenter_user_id: int,
        content: str,
        parent_comment_id: int | None = None,
    ) -> Comment:
        """Persist a new comment (optionally a reply to `parent_comment_id`) and return it."""

    def find_comment_by_id(self, comment_id: int) -> Comment | None:
        """Return the comment with the given id, or None if no such comment exists."""

    def find_comment_thread_for_post(self, post_id: int) -> list[CommentThreadEntry]:
        """Return every comment on `post_id`, depth-first: each reply follows its parent."""

    def delete_comment(self, comment_id: int, commenter_user_id: int) -> None:
        """Delete a comment; only `commenter_user_id` may delete their own comment."""


class PostgresCommentRepository:
    """Implements `CommentRepository` against PostgreSQL via a pooled connection."""

    def __init__(self, connection_pool: PostgresConnectionPool) -> None:
        self._connection_pool = connection_pool

    def create_comment(
        self,
        post_id: int,
        commenter_user_id: int,
        content: str,
        parent_comment_id: int | None = None,
    ) -> Comment:
        """Insert a new comment row and return the created entity."""
        try:
            with self._connection_pool.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO comments
                        (post_id, commenter_user_id, parent_comment_id, content)
                    VALUES
                        (%(post_id)s, %(commenter_user_id)s, %(parent_comment_id)s, %(content)s)
                    RETURNING
                        comment_id, post_id, commenter_user_id, parent_comment_id, content,
                        created_at
                    """,
                    {
                        "post_id": post_id,
                        "commenter_user_id": commenter_user_id,
                        "parent_comment_id": parent_comment_id,
                        "content": content,
                    },
                )
                row = cursor.fetchone()
        except psycopg2.errors.ForeignKeyViolation as violation:
            constraint_name = violation.diag.constraint_name or ""
            if "post_id" in constraint_name:
                raise PostNotFoundError(f"No post with id {post_id!r} exists.") from violation
            if "parent_comment_id" in constraint_name:
                raise CommentNotFoundError(
                    f"No comment with id {parent_comment_id!r} exists."
                ) from violation
            raise UserNotFoundError(f"No user with id {commenter_user_id!r} exists.") from violation
        assert row is not None  # RETURNING always yields exactly one row on a successful insert
        return _row_to_comment(row)

    def find_comment_by_id(self, comment_id: int) -> Comment | None:
        """Look up a comment by id, returning None if no such comment exists."""
        with self._connection_pool.cursor() as cursor:
            cursor.execute(
                """
                SELECT comment_id, post_id, commenter_user_id, parent_comment_id, content,
                       created_at
                FROM comments
                WHERE comment_id = %(comment_id)s
                """,
                {"comment_id": comment_id},
            )
            row = cursor.fetchone()
        return _row_to_comment(row) if row is not None else None

    def find_comment_thread_for_post(self, post_id: int) -> list[CommentThreadEntry]:
        """Return every comment on `post_id` in depth-first thread order.

        A recursive CTE walks the self-referencing `parent_comment_id` adjacency list one
        level at a time, building a sort path so each reply is ordered immediately after
        its parent (and before any of the parent's later siblings), whatever the thread's
        depth turns out to be.
        """
        with self._connection_pool.cursor() as cursor:
            cursor.execute(
                """
                WITH RECURSIVE comment_thread AS (
                    SELECT
                        comment_id, post_id, commenter_user_id, parent_comment_id, content,
                        created_at, 0 AS depth,
                        ARRAY[comment_id] AS sort_path
                    FROM comments
                    WHERE post_id = %(post_id)s AND parent_comment_id IS NULL

                    UNION ALL

                    SELECT
                        child.comment_id, child.post_id, child.commenter_user_id,
                        child.parent_comment_id, child.content, child.created_at,
                        parent.depth + 1,
                        parent.sort_path || ARRAY[child.comment_id]
                    FROM comments AS child
                    JOIN comment_thread AS parent
                        ON child.parent_comment_id = parent.comment_id
                )
                SELECT
                    comment_id, post_id, commenter_user_id, parent_comment_id, content,
                    created_at, depth
                FROM comment_thread
                ORDER BY sort_path
                """,
                {"post_id": post_id},
            )
            rows = cursor.fetchall()
        return [
            CommentThreadEntry(comment=_row_to_comment(row), depth=row["depth"]) for row in rows
        ]

    def delete_comment(self, comment_id: int, commenter_user_id: int) -> None:
        """Delete a comment in one transaction, scoped to its author as defense in depth.

        The service layer already checks ownership before calling this (for a clean
        domain error); the `commenter_user_id` filter here is a backstop.
        """
        with self._connection_pool.cursor() as cursor:
            cursor.execute(
                """
                DELETE FROM comments
                WHERE comment_id = %(comment_id)s AND commenter_user_id = %(commenter_user_id)s
                """,
                {"comment_id": comment_id, "commenter_user_id": commenter_user_id},
            )
            rows_deleted = cursor.rowcount
        if not rows_deleted:
            raise CommentNotFoundError(
                f"No comment with id {comment_id!r} owned by {commenter_user_id!r}."
            )


def _row_to_comment(row: dict[str, Any]) -> Comment:
    return Comment(
        comment_id=row["comment_id"],
        post_id=row["post_id"],
        commenter_user_id=row["commenter_user_id"],
        parent_comment_id=row["parent_comment_id"],
        content=row["content"],
        created_at=row["created_at"],
    )
