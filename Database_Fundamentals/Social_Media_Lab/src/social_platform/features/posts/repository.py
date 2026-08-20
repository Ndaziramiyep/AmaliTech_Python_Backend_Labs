"""Post persistence: the `PostRepository` contract and its PostgreSQL implementation."""

from __future__ import annotations

from typing import Any, Protocol

import psycopg2.errors
from psycopg2.extras import Json

from social_platform.common.exceptions import PostNotFoundError, UserNotFoundError
from social_platform.common.postgres_pool import PostgresConnectionPool
from social_platform.features.posts.model import Post, PostMetadata


class PostRepository(Protocol):
    """Persistence contract for posts. Services depend on this, not on Postgres."""

    def create_post(self, author_user_id: int, content: str, metadata: PostMetadata) -> Post:
        """Persist a new post and return the created entity."""

    def find_post_by_id(self, post_id: int) -> Post | None:
        """Return the post with the given id, or None if no such post exists."""

    def find_posts_by_author(self, author_user_id: int, result_limit: int) -> list[Post]:
        """Return `author_user_id`'s own posts, newest first."""

    def update_post(
        self, post_id: int, author_user_id: int, content: str, metadata: PostMetadata
    ) -> Post:
        """Replace a post's content/metadata; only `author_user_id` may update their own post."""

    def delete_post(self, post_id: int, author_user_id: int) -> None:
        """Delete a post; only `author_user_id` may delete their own post."""

    def count_posts_by_author(self, author_user_id: int) -> int:
        """Return how many posts `author_user_id` has authored."""


class PostgresPostRepository:
    """Implements `PostRepository` against PostgreSQL via a pooled connection."""

    def __init__(self, connection_pool: PostgresConnectionPool) -> None:
        self._connection_pool = connection_pool

    def create_post(self, author_user_id: int, content: str, metadata: PostMetadata) -> Post:
        """Insert a new post row and return the created entity."""
        try:
            with self._connection_pool.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO posts (author_user_id, content, metadata)
                    VALUES (%(author_user_id)s, %(content)s, %(metadata)s)
                    RETURNING post_id, author_user_id, content, metadata, created_at
                    """,
                    {
                        "author_user_id": author_user_id,
                        "content": content,
                        "metadata": Json(metadata),
                    },
                )
                row = cursor.fetchone()
        except psycopg2.errors.ForeignKeyViolation as violation:
            raise UserNotFoundError(f"No user with id {author_user_id!r} exists.") from violation
        assert row is not None  # RETURNING always yields exactly one row on a successful insert
        return _row_to_post(row)

    def find_post_by_id(self, post_id: int) -> Post | None:
        """Look up a post by id, returning None if no such post exists."""
        with self._connection_pool.cursor() as cursor:
            cursor.execute(
                """
                SELECT post_id, author_user_id, content, metadata, created_at
                FROM posts
                WHERE post_id = %(post_id)s
                """,
                {"post_id": post_id},
            )
            row = cursor.fetchone()
        return _row_to_post(row) if row is not None else None

    def find_posts_by_author(self, author_user_id: int, result_limit: int) -> list[Post]:
        """Return `author_user_id`'s own posts, newest first."""
        with self._connection_pool.cursor() as cursor:
            cursor.execute(
                """
                SELECT post_id, author_user_id, content, metadata, created_at
                FROM posts
                WHERE author_user_id = %(author_user_id)s
                ORDER BY created_at DESC, post_id DESC
                LIMIT %(result_limit)s
                """,
                {"author_user_id": author_user_id, "result_limit": result_limit},
            )
            rows = cursor.fetchall()
        return [_row_to_post(row) for row in rows]

    def update_post(
        self, post_id: int, author_user_id: int, content: str, metadata: PostMetadata
    ) -> Post:
        """Update a post in one transaction, scoped to its author as defense in depth.

        The service layer already checks ownership before calling this (for a clean
        domain error); the `author_user_id` filter here is a backstop, the same
        "service checks first, the query itself is the last line of defense" pattern
        used throughout this codebase.
        """
        with self._connection_pool.cursor() as cursor:
            cursor.execute(
                """
                UPDATE posts
                SET content = %(content)s, metadata = %(metadata)s
                WHERE post_id = %(post_id)s AND author_user_id = %(author_user_id)s
                RETURNING post_id, author_user_id, content, metadata, created_at
                """,
                {
                    "post_id": post_id,
                    "author_user_id": author_user_id,
                    "content": content,
                    "metadata": Json(metadata),
                },
            )
            row = cursor.fetchone()
        if row is None:
            raise PostNotFoundError(f"No post with id {post_id!r} owned by {author_user_id!r}.")
        return _row_to_post(row)

    def delete_post(self, post_id: int, author_user_id: int) -> None:
        """Delete a post in one transaction, scoped to its author as defense in depth."""
        with self._connection_pool.cursor() as cursor:
            cursor.execute(
                """
                DELETE FROM posts
                WHERE post_id = %(post_id)s AND author_user_id = %(author_user_id)s
                """,
                {"post_id": post_id, "author_user_id": author_user_id},
            )
            rows_deleted = cursor.rowcount
        if not rows_deleted:
            raise PostNotFoundError(f"No post with id {post_id!r} owned by {author_user_id!r}.")

    def count_posts_by_author(self, author_user_id: int) -> int:
        """Return how many posts `author_user_id` has authored."""
        with self._connection_pool.cursor() as cursor:
            cursor.execute(
                """
                SELECT COUNT(*) AS post_count FROM posts
                WHERE author_user_id = %(author_user_id)s
                """,
                {"author_user_id": author_user_id},
            )
            row = cursor.fetchone()
        assert row is not None  # COUNT(*) always yields exactly one row
        return int(row["post_count"])


def _row_to_post(row: dict[str, Any]) -> Post:
    return Post(
        post_id=row["post_id"],
        author_user_id=row["author_user_id"],
        content=row["content"],
        metadata=row["metadata"],
        created_at=row["created_at"],
    )
