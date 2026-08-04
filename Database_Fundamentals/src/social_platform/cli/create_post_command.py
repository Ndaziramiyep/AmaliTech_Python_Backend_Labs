"""Composition root for the create-post CLI command."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence

from social_platform.cli._composition import build_repository_bundle
from social_platform.models.exceptions import SocialPlatformError
from social_platform.services.post_creation_service import PostCreationService


def main(argv: Sequence[str] | None = None) -> int:
    """Parse arguments and create a new post."""
    parser = argparse.ArgumentParser(description="Create a post.")
    parser.add_argument("author_user_id", type=int)
    parser.add_argument("content")
    parser.add_argument("--tag", dest="tags", action="append", default=None)
    parser.add_argument("--location", default=None)
    parsed_arguments = parser.parse_args(argv)

    repository_bundle = build_repository_bundle()
    post_creation_service = PostCreationService(
        repository_bundle.post_repository, repository_bundle.activity_log_repository
    )
    try:
        post = post_creation_service.create_post(
            parsed_arguments.author_user_id,
            parsed_arguments.content,
            parsed_arguments.tags,
            parsed_arguments.location,
        )
    except SocialPlatformError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    finally:
        repository_bundle.connection_pool.close_all_connections()

    print(f"Created post {post.post_id}.")
    return 0
