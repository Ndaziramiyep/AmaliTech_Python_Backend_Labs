"""Composition root for the add-comment CLI command."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence

from social_platform.cli._composition import build_repository_bundle
from social_platform.models.exceptions import SocialPlatformError
from social_platform.services.comment_creation_service import CommentCreationService


def main(argv: Sequence[str] | None = None) -> int:
    """Parse arguments and add a comment to a post."""
    parser = argparse.ArgumentParser(description="Add a comment to a post.")
    parser.add_argument("post_id", type=int)
    parser.add_argument("commenter_user_id", type=int)
    parser.add_argument("content")
    parsed_arguments = parser.parse_args(argv)

    repository_bundle = build_repository_bundle()
    comment_creation_service = CommentCreationService(
        repository_bundle.comment_repository, repository_bundle.activity_log_repository
    )
    try:
        comment = comment_creation_service.create_comment(
            parsed_arguments.post_id,
            parsed_arguments.commenter_user_id,
            parsed_arguments.content,
        )
    except SocialPlatformError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    finally:
        repository_bundle.connection_pool.close_all_connections()

    print(f"Created comment {comment.comment_id}.")
    return 0
