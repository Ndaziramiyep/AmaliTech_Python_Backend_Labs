"""Composition root for the unfollow-user CLI command."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence

from social_platform.cli._composition import build_repository_bundle
from social_platform.models.exceptions import SocialPlatformError
from social_platform.services.user_following_service import UserFollowingService


def main(argv: Sequence[str] | None = None) -> int:
    """Parse arguments and unfollow one user on behalf of another."""
    parser = argparse.ArgumentParser(description="Unfollow a user.")
    parser.add_argument("follower_user_id", type=int)
    parser.add_argument("followee_user_id", type=int)
    parsed_arguments = parser.parse_args(argv)

    repository_bundle = build_repository_bundle()
    following_service = UserFollowingService(
        repository_bundle.follower_repository, repository_bundle.activity_log_repository
    )
    try:
        result = following_service.unfollow_user(
            parsed_arguments.follower_user_id, parsed_arguments.followee_user_id
        )
    except SocialPlatformError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    finally:
        repository_bundle.connection_pool.close_all_connections()

    print(f"Unfollow result: {result.value}")
    return 0
