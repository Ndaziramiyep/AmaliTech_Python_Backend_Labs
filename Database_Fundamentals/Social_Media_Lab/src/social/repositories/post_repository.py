"""Data access for the posts table. No business logic, no commits."""
from typing import Any, Optional, Sequence

import psycopg2
from psycopg2.extras import Json

from social.exceptions import UserNotFoundError
from social.models import Post


class PostgresPostRepository:
    """Postgres-backed persistence for posts."""

    def create(self, cursor: Any, post: Post) -> Post:
        """Inserts a new post and returns the stored row."""
        try:
            cursor.execute(
                """
                INSERT INTO posts (author_id, body, metadata)
                VALUES (%s, %s, %s)
                RETURNING id, author_id, body, metadata, created_at
                """,
                (post.author_id, post.body, Json(dict(post.metadata))),
            )
        except psycopg2.errors.ForeignKeyViolation as exc:
            raise UserNotFoundError(f"No user with id {post.author_id}.") from exc
        return _row_to_post(cursor.fetchone())

    def get_by_id(self, cursor: Any, post_id: int) -> Optional[Post]:
        """Returns the post with the given id, or None if it does not exist."""
        cursor.execute(
            "SELECT id, author_id, body, metadata, created_at FROM posts WHERE id = %s",
            (post_id,),
        )
        row = cursor.fetchone()
        return _row_to_post(row) if row else None

    def delete(self, cursor: Any, post_id: int) -> None:
        """Deletes the post with the given id."""
        cursor.execute("DELETE FROM posts WHERE id = %s", (post_id,))

    def list_recent(self, cursor: Any, limit: int) -> Sequence[Post]:
        """Returns the most recently created posts, up to the given limit."""
        cursor.execute(
            """
            SELECT id, author_id, body, metadata, created_at
            FROM posts
            ORDER BY created_at DESC, id DESC
            LIMIT %s
            """,
            (limit,),
        )
        return [_row_to_post(row) for row in cursor.fetchall()]


def _row_to_post(row: Any) -> Post:
    """Converts a raw database row into a Post."""
    post_id, author_id, body, metadata, created_at = row
    return Post(
        id=post_id,
        author_id=author_id,
        body=body,
        metadata=metadata,
        created_at=created_at,
    )
