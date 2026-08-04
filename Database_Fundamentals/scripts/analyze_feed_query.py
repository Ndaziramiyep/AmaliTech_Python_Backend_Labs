#!/usr/bin/env python
"""Run EXPLAIN ANALYZE on the timeline feed query with and without its supporting index."""

from __future__ import annotations

from social_platform.config.application_settings import ApplicationSettings
from social_platform.database.postgres_connection_pool import PostgresConnectionPool
from social_platform.repositories.postgres_post_repository import _FEED_QUERY

_SAMPLE_FOLLOWER_USER_ID = 1
_FEED_INDEX_NAME = "idx_posts_author_created_at"


def main() -> int:
    """Print the feed query's plan with the index present, then again after dropping it."""
    settings = ApplicationSettings.from_environment()
    connection_pool = PostgresConnectionPool(settings.postgres)

    print(f"--- EXPLAIN ANALYZE with {_FEED_INDEX_NAME} ---")
    _print_feed_query_plan(connection_pool)

    print(f"\n--- EXPLAIN ANALYZE after dropping {_FEED_INDEX_NAME} ---")
    with connection_pool.cursor() as cursor:
        cursor.execute(f"DROP INDEX IF EXISTS {_FEED_INDEX_NAME}")
    _print_feed_query_plan(connection_pool)

    print(f"\nRestoring {_FEED_INDEX_NAME}...")
    with connection_pool.cursor() as cursor:
        cursor.execute(
            f"CREATE INDEX {_FEED_INDEX_NAME} ON posts (author_user_id, created_at DESC)"
        )

    connection_pool.close_all_connections()
    return 0


def _print_feed_query_plan(connection_pool: PostgresConnectionPool) -> None:
    with connection_pool.cursor() as cursor:
        cursor.execute(
            f"EXPLAIN ANALYZE {_FEED_QUERY}",
            {"follower_user_id": _SAMPLE_FOLLOWER_USER_ID, "first_row": 1, "last_row": 20},
        )
        for row in cursor.fetchall():
            print(row["QUERY PLAN"])


if __name__ == "__main__":
    raise SystemExit(main())
