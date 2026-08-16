"""The timeline feed query: two CTEs, a JOIN, and `ROW_NUMBER()` for stable pagination.

Backed by `idx_posts_author_created_at (author_user_id, created_at DESC)`, which turns
the join-then-sort into an index scan feeding the window function directly instead of a
sequential scan over `posts` plus an explicit sort. See `scripts/analyze_feed_query.py`
for an `EXPLAIN ANALYZE` comparison with and without that index.
"""

from __future__ import annotations

from typing import Any, Protocol

from social_platform.common.postgres_pool import PostgresConnectionPool
from social_platform.features.feed.model import FeedPostEntry

FEED_QUERY = """
WITH followed_users AS (
    SELECT followee_user_id
    FROM followers
    WHERE follower_user_id = %(follower_user_id)s
),
timeline_posts AS (
    SELECT
        posts.post_id,
        posts.author_user_id,
        posts.content,
        posts.metadata,
        posts.created_at,
        ROW_NUMBER() OVER (ORDER BY posts.created_at DESC, posts.post_id DESC) AS row_number
    FROM posts
    JOIN followed_users ON followed_users.followee_user_id = posts.author_user_id
)
SELECT
    timeline_posts.post_id,
    timeline_posts.author_user_id,
    users.username AS author_username,
    timeline_posts.content,
    timeline_posts.metadata,
    timeline_posts.created_at
FROM timeline_posts
JOIN users ON users.user_id = timeline_posts.author_user_id
WHERE timeline_posts.row_number BETWEEN %(first_row)s AND %(last_row)s
ORDER BY timeline_posts.row_number
"""


class FeedRepository(Protocol):
    """Read contract for the timeline feed. Services depend on this, not on Postgres."""

    def fetch_feed_page(
        self, follower_user_id: int, first_row: int, last_row: int
    ) -> list[FeedPostEntry]:
        """Return one paginated, chronologically ordered page of a user's timeline feed."""


class PostgresFeedRepository:
    """Implements `FeedRepository` against PostgreSQL via a pooled connection."""

    def __init__(self, connection_pool: PostgresConnectionPool) -> None:
        self._connection_pool = connection_pool

    def fetch_feed_page(
        self, follower_user_id: int, first_row: int, last_row: int
    ) -> list[FeedPostEntry]:
        """Return one paginated page of `follower_user_id`'s timeline feed, newest first."""
        with self._connection_pool.cursor() as cursor:
            cursor.execute(
                FEED_QUERY,
                {
                    "follower_user_id": follower_user_id,
                    "first_row": first_row,
                    "last_row": last_row,
                },
            )
            rows = cursor.fetchall()
        return [_row_to_feed_post_entry(row) for row in rows]


def _row_to_feed_post_entry(row: dict[str, Any]) -> FeedPostEntry:
    return FeedPostEntry(
        post_id=row["post_id"],
        author_user_id=row["author_user_id"],
        author_username=row["author_username"],
        content=row["content"],
        metadata=row["metadata"],
        created_at=row["created_at"],
    )
