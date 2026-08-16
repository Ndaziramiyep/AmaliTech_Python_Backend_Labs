"""The trending-posts query: recent posts ranked by their comment count."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Protocol

from social_platform.common.postgres_pool import PostgresConnectionPool
from social_platform.features.trending.model import TrendingPostEntry

TRENDING_QUERY = """
WITH recent_posts AS (
    SELECT post_id, author_user_id, content, metadata, created_at
    FROM posts
    WHERE created_at >= %(since)s
),
comment_counts AS (
    SELECT post_id, COUNT(*) AS comment_count
    FROM comments
    WHERE post_id IN (SELECT post_id FROM recent_posts)
    GROUP BY post_id
)
SELECT
    recent_posts.post_id,
    recent_posts.author_user_id,
    recent_posts.content,
    recent_posts.metadata,
    recent_posts.created_at,
    COALESCE(comment_counts.comment_count, 0) AS comment_count
FROM recent_posts
LEFT JOIN comment_counts ON comment_counts.post_id = recent_posts.post_id
ORDER BY comment_count DESC, recent_posts.created_at DESC
LIMIT %(result_limit)s
"""


class TrendingRepository(Protocol):
    """Read contract for trending posts. Services depend on this, not on Postgres."""

    def fetch_trending_posts(self, since: datetime, result_limit: int) -> list[TrendingPostEntry]:
        """Return posts created since `since`, ranked by their recent comment count."""


class PostgresTrendingRepository:
    """Implements `TrendingRepository` against PostgreSQL via a pooled connection."""

    def __init__(self, connection_pool: PostgresConnectionPool) -> None:
        self._connection_pool = connection_pool

    def fetch_trending_posts(self, since: datetime, result_limit: int) -> list[TrendingPostEntry]:
        """Return posts created since `since`, most-commented first."""
        with self._connection_pool.cursor() as cursor:
            cursor.execute(TRENDING_QUERY, {"since": since, "result_limit": result_limit})
            rows = cursor.fetchall()
        return [_row_to_trending_post_entry(row) for row in rows]


def _row_to_trending_post_entry(row: dict[str, Any]) -> TrendingPostEntry:
    return TrendingPostEntry(
        post_id=row["post_id"],
        author_user_id=row["author_user_id"],
        content=row["content"],
        metadata=row["metadata"],
        created_at=row["created_at"],
        comment_count=row["comment_count"],
    )
