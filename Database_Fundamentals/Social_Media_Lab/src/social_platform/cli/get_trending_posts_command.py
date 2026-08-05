"""Composition root for the get-trending-posts CLI command."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from datetime import UTC, datetime, timedelta

from social_platform.cli._composition import build_repository_bundle
from social_platform.models.entities import TrendingPostEntry
from social_platform.services.trending_posts_service import TrendingPostsService


def main(argv: Sequence[str] | None = None) -> int:
    """Parse arguments and print the most-commented recent posts."""
    parser = argparse.ArgumentParser(description="Show trending posts.")
    parser.add_argument("--since-hours", type=int, default=24)
    parser.add_argument("--limit", type=int, default=10)
    parsed_arguments = parser.parse_args(argv)

    repository_bundle = build_repository_bundle()
    trending_service = TrendingPostsService(repository_bundle.post_repository)
    since = datetime.now(UTC) - timedelta(hours=parsed_arguments.since_hours)
    try:
        trending_posts = trending_service.get_trending_posts(since, parsed_arguments.limit)
    finally:
        repository_bundle.connection_pool.close_all_connections()

    if not trending_posts:
        print("No trending posts to show.")
        return 0
    for entry in trending_posts:
        _print_trending_entry(entry)
    return 0


def _print_trending_entry(entry: TrendingPostEntry) -> None:
    print(f"({entry.comment_count} comments) {entry.content}")
