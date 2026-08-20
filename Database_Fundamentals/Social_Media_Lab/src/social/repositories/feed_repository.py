"""Data access for the feed timeline. No business logic, no commits.

The query itself is also kept standalone at queries/feed_timeline.sql for
the EXPLAIN ANALYZE writeup in docs/schema_design.md.
"""
from typing import Any, Sequence

from social.domain.models import Post


class PostgresFeedRepository:
    def get_timeline(self, cursor: Any, follower_id: int, limit: int) -> Sequence[Post]:
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
    post_id, author_id, body, metadata, created_at = row
    return Post(
        id=post_id,
        author_id=author_id,
        body=body,
        metadata=metadata,
        created_at=created_at,
    )
