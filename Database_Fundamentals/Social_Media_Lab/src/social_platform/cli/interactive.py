"""A menu-driven, interactive front end for the social platform CLI.

Presents a login/register gate, then a numbered action menu that uses the logged-in
user as the actor for every subsequent action.
"""

from __future__ import annotations

from collections.abc import Callable
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
from social_platform.features.users.model import User
from social_platform.features.users.service import UserService

InputFunction = Callable[[str], str]

_GUEST_MENU = """
1. Login
2. Register
3. Exit"""

_ACTION_MENU = """
1. Create post
2. Follow user
3. Unfollow user
4. Add comment
5. Like post
6. View my feed
7. View trending posts
8. Logout
9. Exit"""


def run_interactive_session(
    input_function: InputFunction = input,
    app_context_factory: Callable[[], AppContext] = build_app_context,
) -> int:
    """Run the menu-driven CLI loop until the user exits or input is exhausted."""
    context = app_context_factory()
    try:
        return _run_guest_loop(input_function, context)
    except EOFError:
        print()
        return 0
    finally:
        context.connection_pool.close_all_connections()


def _run_guest_loop(input_function: InputFunction, context: AppContext) -> int:
    while True:
        print(_GUEST_MENU)
        choice = input_function("Choose an option: ").strip()

        if choice == "1":
            user = _handle_login(input_function, context)
        elif choice == "2":
            user = _handle_register(input_function, context)
        elif choice == "3":
            return 0
        else:
            print("Invalid option. Please choose 1, 2, or 3.")
            continue

        if user is not None and _run_action_loop(input_function, context, user):
            return 0


def _handle_login(input_function: InputFunction, context: AppContext) -> User | None:
    username = _prompt_required(input_function, "Username: ")
    password = _prompt_required(input_function, "Password: ")

    user_service = UserService(context.user_repository)
    try:
        user = user_service.login(username, password)
    except SocialPlatformError as error:
        print(f"Error: {error}")
        return None

    print(f"Welcome back, @{user.username}!")
    return user


def _handle_register(input_function: InputFunction, context: AppContext) -> User | None:
    username = _prompt_required(input_function, "Choose a username (3-30 letters/digits/_): ")
    email = _prompt_required(input_function, "Email: ")
    password = _prompt_password_with_confirmation(input_function)

    user_service = UserService(context.user_repository)
    try:
        user = user_service.register(username, email, password)
    except SocialPlatformError as error:
        print(f"Error: {error}")
        return None

    print(f"Registered user {user.user_id} (@{user.username}). You are now logged in.")
    return user


def _prompt_password_with_confirmation(input_function: InputFunction) -> str:
    """Prompt for a password twice, re-prompting both until the two entries match."""
    while True:
        password = _prompt_required(
            input_function,
            "Choose a password (8+ chars, upper, lower, digit, special character): ",
        )
        confirmation = _prompt_required(input_function, "Confirm password: ")
        if password == confirmation:
            return password
        print("Passwords do not match. Please try again.")


def _run_action_loop(input_function: InputFunction, context: AppContext, user: User) -> bool:
    """Run the post-login action menu; returns True if the user chose to exit the program."""
    actions: dict[str, Callable[[], None]] = {
        "1": lambda: _handle_create_post(input_function, context, user),
        "2": lambda: _handle_follow_user(input_function, context, user),
        "3": lambda: _handle_unfollow_user(input_function, context, user),
        "4": lambda: _handle_add_comment(input_function, context, user),
        "5": lambda: _handle_like_post(input_function, context, user),
        "6": lambda: _handle_view_feed(input_function, context, user),
        "7": lambda: _handle_view_trending(input_function, context),
    }

    while True:
        print(_ACTION_MENU)
        choice = input_function(f"[{user.username}] Choose an option: ").strip()

        if choice == "8":
            print("Logged out.")
            return False
        if choice == "9":
            return True

        action = actions.get(choice)
        if action is None:
            print("Invalid option. Please choose a number from 1 to 9.")
            continue
        action()


def _handle_create_post(input_function: InputFunction, context: AppContext, user: User) -> None:
    content = _prompt_required(input_function, "Post content: ")
    tags_input = input_function("Tags (comma-separated, optional): ").strip()
    tags = [tag.strip() for tag in tags_input.split(",") if tag.strip()] or None
    location = input_function("Location (optional): ").strip() or None

    post_service = PostService(context.post_repository, context.activity_log_repository)
    try:
        post = post_service.create_post(user.user_id, content, tags, location)
    except SocialPlatformError as error:
        print(f"Error: {error}")
        return
    print(f"Created post {post.post_id}.")


def _handle_follow_user(input_function: InputFunction, context: AppContext, user: User) -> None:
    followee_user_id = _prompt_int(input_function, "User id to follow: ")
    follow_service = FollowService(context.follower_repository, context.activity_log_repository)
    try:
        result = follow_service.follow_user(user.user_id, followee_user_id)
    except SocialPlatformError as error:
        print(f"Error: {error}")
        return
    print(f"Follow result: {result.value}")


def _handle_unfollow_user(input_function: InputFunction, context: AppContext, user: User) -> None:
    followee_user_id = _prompt_int(input_function, "User id to unfollow: ")
    follow_service = FollowService(context.follower_repository, context.activity_log_repository)
    try:
        result = follow_service.unfollow_user(user.user_id, followee_user_id)
    except SocialPlatformError as error:
        print(f"Error: {error}")
        return
    print(f"Unfollow result: {result.value}")


def _handle_add_comment(input_function: InputFunction, context: AppContext, user: User) -> None:
    post_id = _select_post_id(input_function, context, user, "comment on")
    if post_id is None:
        return
    content = _prompt_required(input_function, "Comment: ")

    comment_service = CommentService(context.comment_repository, context.activity_log_repository)
    try:
        comment = comment_service.create_comment(post_id, user.user_id, content)
    except SocialPlatformError as error:
        print(f"Error: {error}")
        return
    print(f"Created comment {comment.comment_id}.")


def _handle_like_post(input_function: InputFunction, context: AppContext, user: User) -> None:
    post_id = _select_post_id(input_function, context, user, "like")
    if post_id is None:
        return

    engagement_service = EngagementService(context.post_repository, context.activity_log_repository)
    try:
        engagement_service.like_post(user.user_id, post_id)
    except SocialPlatformError as error:
        print(f"Error: {error}")
        return
    print("Post liked.")


def _select_post_id(
    input_function: InputFunction, context: AppContext, user: User, action_verb: str
) -> int | None:
    """Show the user's feed as a numbered list and let them pick a post to act on."""
    feed_service = FeedService(context.feed_repository, context.timeline_cache)
    feed_page = feed_service.get_user_feed_page(user.user_id, 1)
    if not feed_page:
        print(f"No posts available to {action_verb} yet. Follow someone first.")
        return None

    print("Available posts:")
    for index, entry in enumerate(feed_page, start=1):
        print(f"{index}. @{entry.author_username}: {entry.content}")

    prompt = f"Choose a post to {action_verb} (1-{len(feed_page)}): "
    choice = _prompt_int(input_function, prompt)
    while choice < 1 or choice > len(feed_page):
        print(f"Please enter a number from 1 to {len(feed_page)}.")
        choice = _prompt_int(input_function, prompt)
    return feed_page[choice - 1].post_id


def _handle_view_feed(input_function: InputFunction, context: AppContext, user: User) -> None:
    page = _prompt_int(input_function, "Page number (default 1): ", default=1)

    feed_service = FeedService(context.feed_repository, context.timeline_cache)
    feed_page = feed_service.get_user_feed_page(user.user_id, page)
    if not feed_page:
        print("No posts to show.")
        return
    for entry in feed_page:
        _print_feed_entry(entry)


def _handle_view_trending(input_function: InputFunction, context: AppContext) -> None:
    since_hours = _prompt_int(
        input_function, "Show posts from the last N hours (default 24): ", default=24
    )
    limit = _prompt_int(input_function, "Max results (default 10): ", default=10)

    trending_service = TrendingService(context.trending_repository)
    since = datetime.now(UTC) - timedelta(hours=since_hours)
    trending_posts = trending_service.get_trending_posts(since, limit)
    if not trending_posts:
        print("No trending posts to show.")
        return
    for entry in trending_posts:
        _print_trending_entry(entry)


def _print_feed_entry(entry: FeedPostEntry) -> None:
    print(f"[{entry.created_at:%Y-%m-%d %H:%M}] @{entry.author_username}: {entry.content}")


def _print_trending_entry(entry: TrendingPostEntry) -> None:
    print(f"({entry.comment_count} comments) {entry.content}")


def _prompt_required(input_function: InputFunction, prompt: str) -> str:
    while True:
        value = input_function(prompt).strip()
        if value:
            return value
        print("This field is required.")


def _prompt_int(input_function: InputFunction, prompt: str, default: int | None = None) -> int:
    while True:
        raw_value = input_function(prompt).strip()
        if not raw_value and default is not None:
            return default
        try:
            return int(raw_value)
        except ValueError:
            print("Please enter a whole number.")
