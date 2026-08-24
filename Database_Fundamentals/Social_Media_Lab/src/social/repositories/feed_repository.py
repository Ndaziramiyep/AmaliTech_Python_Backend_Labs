"""Data access for the feed timeline, with the query also kept standalone at queries/feed_timeline.sql for the EXPLAIN ANALYZE writeup in docs/schema_design.md."""
from typing import Any, Sequence

from social.models import Post


class PostgresFeedRepository:
    """Postgres-backed persistence for a user's feed timeline."""

    def get_timeline(self, cursor: Any, follower_id: int, limit: int) -> Sequence[Post]:
        """Returns the most recent posts from users the given follower follows."""
        cursor.execute(
            """
            SELECT p.id, p.author_id, p.body, p.metadata, p.created_at
            FROM posts p
            JOIN followers f ON f.followee_id = p.author_id
            WHERE f.follower_id = %s
            ORDER BY p.created_at DESC, p.id DESC
            LIMIT %s
            """,
            (follower_id, limit),
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
