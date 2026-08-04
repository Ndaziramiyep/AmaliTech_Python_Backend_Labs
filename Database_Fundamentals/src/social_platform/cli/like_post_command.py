"""Composition root for the like-post CLI command."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence

from social_platform.cli._composition import build_repository_bundle
from social_platform.models.exceptions import SocialPlatformError
from social_platform.services.post_engagement_service import PostEngagementService


def main(argv: Sequence[str] | None = None) -> int:
    """Parse arguments and record a like on a post."""
    parser = argparse.ArgumentParser(description="Like a post.")
    parser.add_argument("actor_user_id", type=int)
    parser.add_argument("post_id", type=int)
    parsed_arguments = parser.parse_args(argv)

    repository_bundle = build_repository_bundle()
    engagement_service = PostEngagementService(
        repository_bundle.post_repository, repository_bundle.activity_log_repository
    )
    try:
        engagement_service.like_post(parsed_arguments.actor_user_id, parsed_arguments.post_id)
    except SocialPlatformError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    finally:
        repository_bundle.connection_pool.close_all_connections()

    print("Post liked.")
    return 0
