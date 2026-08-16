"""The scriptable command-line interface: one argparse subcommand per user action.

Every subcommand builds the small slice of services it needs from the shared
`AppContext`, runs the action, and reports success -- or a clean, one-line domain
error, never a raw traceback.
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from datetime import UTC, datetime, timedelta

from social_platform.cli.app_context import AppContext, build_app_context
from social_platform.common.exceptions import SocialPlatformError
from social_platform.features.comments.service import CommentService
from social_platform.features.engagement.service import EngagementService
from social_platform.features.feed.model import FeedPostEntry
from social_platform.features.feed.service import FeedService
from social_platform.features.followers.service import FollowService
from social_platform.features.posts.service import PostService
from social_platform.features.trending.model import TrendingPostEntry
from social_platform.features.trending.service import TrendingService
from social_platform.features.users.service import UserService


def main(argv: Sequence[str] | None = None) -> int:
    """Parse arguments and run the requested subcommand."""
    parser = _build_parser()
    arguments = parser.parse_args(argv)
    if arguments.handler is None:
        parser.print_help()
        return 1

    context = build_app_context()
    try:
        arguments.handler(arguments, context)
    except SocialPlatformError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    finally:
        context.connection_pool.close_all_connections()
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Social media platform CLI.")
    parser.set_defaults(handler=None)
    subparsers = parser.add_subparsers(dest="command")

    register_user = subparsers.add_parser("register-user", help="Register a new user.")
    register_user.add_argument("username")
    register_user.add_argument("email")
    register_user.add_argument("password")
    register_user.add_argument("display_name")
    register_user.set_defaults(handler=_register_user)

    create_post = subparsers.add_parser("create-post", help="Create a post.")
    create_post.add_argument("author_user_id", type=int)
    create_post.add_argument("content")
    create_post.add_argument("--tag", dest="tags", action="append", default=None)
    create_post.add_argument("--location", default=None)
    create_post.set_defaults(handler=_create_post)

    follow_user = subparsers.add_parser("follow-user", help="Follow a user.")
    follow_user.add_argument("follower_user_id", type=int)
    follow_user.add_argument("followee_user_id", type=int)
    follow_user.set_defaults(handler=_follow_user)

    unfollow_user = subparsers.add_parser("unfollow-user", help="Unfollow a user.")
    unfollow_user.add_argument("follower_user_id", type=int)
    unfollow_user.add_argument("followee_user_id", type=int)
    unfollow_user.set_defaults(handler=_unfollow_user)

    add_comment = subparsers.add_parser("add-comment", help="Add a comment to a post.")
    add_comment.add_argument("post_id", type=int)
    add_comment.add_argument("commenter_user_id", type=int)
    add_comment.add_argument("content")
    add_comment.set_defaults(handler=_add_comment)

    like_post = subparsers.add_parser("like-post", help="Like a post.")
    like_post.add_argument("actor_user_id", type=int)
    like_post.add_argument("post_id", type=int)
    like_post.set_defaults(handler=_like_post)

    get_user_feed = subparsers.add_parser("get-user-feed", help="Show a user's timeline feed.")
    get_user_feed.add_argument("follower_user_id", type=int)
    get_user_feed.add_argument("--page", type=int, default=1)
    get_user_feed.set_defaults(handler=_get_user_feed)

    get_trending_posts = subparsers.add_parser("get-trending-posts", help="Show trending posts.")
    get_trending_posts.add_argument("--since-hours", type=int, default=24)
    get_trending_posts.add_argument("--limit", type=int, default=10)
    get_trending_posts.set_defaults(handler=_get_trending_posts)

    return parser


def _register_user(arguments: argparse.Namespace, context: AppContext) -> None:
    service = UserService(context.user_repository)
    user = service.register(
        arguments.username, arguments.email, arguments.password, arguments.display_name
    )
    print(f"Registered user {user.user_id} (@{user.username}).")


def _create_post(arguments: argparse.Namespace, context: AppContext) -> None:
    service = PostService(context.post_repository, context.activity_log_repository)
    post = service.create_post(
        arguments.author_user_id, arguments.content, arguments.tags, arguments.location
    )
    print(f"Created post {post.post_id}.")


def _follow_user(arguments: argparse.Namespace, context: AppContext) -> None:
    service = FollowService(context.follower_repository, context.activity_log_repository)
    result = service.follow_user(arguments.follower_user_id, arguments.followee_user_id)
    print(f"Follow result: {result.value}")


def _unfollow_user(arguments: argparse.Namespace, context: AppContext) -> None:
    service = FollowService(context.follower_repository, context.activity_log_repository)
    result = service.unfollow_user(arguments.follower_user_id, arguments.followee_user_id)
    print(f"Unfollow result: {result.value}")


def _add_comment(arguments: argparse.Namespace, context: AppContext) -> None:
    service = CommentService(context.comment_repository, context.activity_log_repository)
    comment = service.create_comment(
        arguments.post_id, arguments.commenter_user_id, arguments.content
    )
    print(f"Created comment {comment.comment_id}.")


def _like_post(arguments: argparse.Namespace, context: AppContext) -> None:
    service = EngagementService(context.post_repository, context.activity_log_repository)
    service.like_post(arguments.actor_user_id, arguments.post_id)
    print("Post liked.")


def _get_user_feed(arguments: argparse.Namespace, context: AppContext) -> None:
    service = FeedService(context.feed_repository, context.timeline_cache)
    feed_page = service.get_user_feed_page(arguments.follower_user_id, arguments.page)
    if not feed_page:
        print("No posts to show.")
        return
    for entry in feed_page:
        _print_feed_entry(entry)


def _get_trending_posts(arguments: argparse.Namespace, context: AppContext) -> None:
    service = TrendingService(context.trending_repository)
    since = datetime.now(UTC) - timedelta(hours=arguments.since_hours)
    trending_posts = service.get_trending_posts(since, arguments.limit)
    if not trending_posts:
        print("No trending posts to show.")
        return
    for entry in trending_posts:
        _print_trending_entry(entry)


def _print_feed_entry(entry: FeedPostEntry) -> None:
    print(f"[{entry.created_at:%Y-%m-%d %H:%M}] @{entry.author_username}: {entry.content}")


def _print_trending_entry(entry: TrendingPostEntry) -> None:
    print(f"({entry.comment_count} comments) {entry.content}")
