"""PostgreSQL-backed persistence for posts, the timeline feed, and trending posts."""

from __future__ import annotations

from datetime import datetime
from typing import Any

import psycopg2.errors
from psycopg2.extras import Json

from social_platform.database.postgres_connection_pool import PostgresConnectionPool
from social_platform.models.entities import FeedPostEntry, Post, PostMetadata, TrendingPostEntry
from social_platform.models.exceptions import UserNotFoundError
from social_platform.repositories.interfaces import PostRepositoryInterface

_FEED_QUERY = """
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

_TRENDING_QUERY = """
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


class PostgresPostRepository(PostRepositoryInterface):
    """Implements `PostRepositoryInterface` against PostgreSQL via a connection pool."""

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

    def fetch_timeline_feed_page(
        self, follower_user_id: int, first_row: int, last_row: int
    ) -> list[FeedPostEntry]:
        """Return one paginated page of `follower_user_id`'s timeline feed, newest first."""
        with self._connection_pool.cursor() as cursor:
            cursor.execute(
                _FEED_QUERY,
                {
                    "follower_user_id": follower_user_id,
                    "first_row": first_row,
                    "last_row": last_row,
                },
            )
            rows = cursor.fetchall()
        return [_row_to_feed_post_entry(row) for row in rows]

    def fetch_trending_posts(self, since: datetime, result_limit: int) -> list[TrendingPostEntry]:
        """Return posts created since `since`, ranked by their recent comment count."""
        with self._connection_pool.cursor() as cursor:
            cursor.execute(_TRENDING_QUERY, {"since": since, "result_limit": result_limit})
            rows = cursor.fetchall()
        return [_row_to_trending_post_entry(row) for row in rows]


def _row_to_post(row: dict[str, Any]) -> Post:
    return Post(
        post_id=row["post_id"],
        author_user_id=row["author_user_id"],
        content=row["content"],
        metadata=row["metadata"],
        created_at=row["created_at"],
    )


def _row_to_feed_post_entry(row: dict[str, Any]) -> FeedPostEntry:
    return FeedPostEntry(
        post_id=row["post_id"],
        author_user_id=row["author_user_id"],
        author_username=row["author_username"],
        content=row["content"],
        metadata=row["metadata"],
        created_at=row["created_at"],
    )


def _row_to_trending_post_entry(row: dict[str, Any]) -> TrendingPostEntry:
    return TrendingPostEntry(
        post_id=row["post_id"],
        author_user_id=row["author_user_id"],
        content=row["content"],
        metadata=row["metadata"],
        created_at=row["created_at"],
        comment_count=row["comment_count"],
    )
