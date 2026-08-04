"""Composition root for the get-user-feed CLI command."""

from __future__ import annotations

import argparse
from collections.abc import Sequence

from social_platform.cli._composition import build_repository_bundle
from social_platform.models.entities import FeedPostEntry
from social_platform.services.user_timeline_feed_service import UserTimelineFeedService


def main(argv: Sequence[str] | None = None) -> int:
    """Parse arguments and print one page of a user's timeline feed."""
    parser = argparse.ArgumentParser(description="Show a user's timeline feed.")
    parser.add_argument("follower_user_id", type=int)
    parser.add_argument("--page", type=int, default=1)
    parsed_arguments = parser.parse_args(argv)

    repository_bundle = build_repository_bundle()
    feed_service = UserTimelineFeedService(
        repository_bundle.post_repository, repository_bundle.timeline_cache_repository
    )
    try:
        feed_page = feed_service.get_user_feed_page(
            parsed_arguments.follower_user_id, parsed_arguments.page
        )
    finally:
        repository_bundle.connection_pool.close_all_connections()

    if not feed_page:
        print("No posts to show.")
        return 0
    for entry in feed_page:
        _print_feed_entry(entry)
    return 0


def _print_feed_entry(entry: FeedPostEntry) -> None:
    print(f"[{entry.created_at:%Y-%m-%d %H:%M}] @{entry.author_username}: {entry.content}")
