"""Data access for the posts table. No business logic, no commits."""
from typing import Any, Optional, Sequence

from psycopg2.extras import Json

from social.models import Post


class PostgresPostRepository:
    def create(self, cursor: Any, post: Post) -> Post:
        cursor.execute(
            """
            INSERT INTO posts (author_id, body, metadata)
            VALUES (%s, %s, %s)
            RETURNING id, author_id, body, metadata, created_at
            """,
            (post.author_id, post.body, Json(dict(post.metadata))),
        )
        return _row_to_post(cursor.fetchone())

    def get_by_id(self, cursor: Any, post_id: int) -> Optional[Post]:
        cursor.execute(
            "SELECT id, author_id, body, metadata, created_at FROM posts WHERE id = %s",
            (post_id,),
        )
        row = cursor.fetchone()
        return _row_to_post(row) if row else None

    def delete(self, cursor: Any, post_id: int) -> None:
        cursor.execute("DELETE FROM posts WHERE id = %s", (post_id,))

    def list_recent(self, cursor: Any, limit: int) -> Sequence[Post]:
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
    post_id, author_id, body, metadata, created_at = row
    return Post(
        id=post_id,
        author_id=author_id,
        body=body,
        metadata=metadata,
        created_at=created_at,
    )
