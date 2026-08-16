"""Post persistence: the `PostRepository` contract and its PostgreSQL implementation."""

from __future__ import annotations

from typing import Any, Protocol

import psycopg2.errors
from psycopg2.extras import Json

from social_platform.common.exceptions import UserNotFoundError
from social_platform.common.postgres_pool import PostgresConnectionPool
from social_platform.features.posts.model import Post, PostMetadata


class PostRepository(Protocol):
    """Persistence contract for posts. Services depend on this, not on Postgres."""

    def create_post(self, author_user_id: int, content: str, metadata: PostMetadata) -> Post:
        """Persist a new post and return the created entity."""

    def find_post_by_id(self, post_id: int) -> Post | None:
        """Return the post with the given id, or None if no such post exists."""


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


def _row_to_post(row: dict[str, Any]) -> Post:
    return Post(
        post_id=row["post_id"],
        author_user_id=row["author_user_id"],
        content=row["content"],
        metadata=row["metadata"],
        created_at=row["created_at"],
    )
