"""A menu-driven, interactive front end for the social platform CLI.

Presents a login/register gate, then a numbered action menu that uses the logged-in
user as the actor for every subsequent action.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime, timedelta

from social_platform.cli._composition import RepositoryBundle, build_repository_bundle
from social_platform.models.entities import FeedPostEntry, TrendingPostEntry, User
from social_platform.models.exceptions import SocialPlatformError
from social_platform.services.comment_creation_service import CommentCreationService
from social_platform.services.post_creation_service import PostCreationService
from social_platform.services.post_engagement_service import PostEngagementService
from social_platform.services.trending_posts_service import TrendingPostsService
from social_platform.services.user_authentication_service import UserAuthenticationService
from social_platform.services.user_following_service import UserFollowingService
from social_platform.services.user_registration_service import UserRegistrationService
from social_platform.services.user_timeline_feed_service import UserTimelineFeedService

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
    repository_bundle_factory: Callable[[], RepositoryBundle] = build_repository_bundle,
) -> int:
    """Run the menu-driven CLI loop until the user exits or input is exhausted."""
    repository_bundle = repository_bundle_factory()
    try:
        return _run_guest_loop(input_function, repository_bundle)
    except EOFError:
        print()
        return 0
    finally:
        repository_bundle.connection_pool.close_all_connections()


def _run_guest_loop(input_function: InputFunction, repository_bundle: RepositoryBundle) -> int:
    while True:
        print(_GUEST_MENU)
        choice = input_function("Choose an option: ").strip()

        if choice == "1":
            user = _handle_login(input_function, repository_bundle)
        elif choice == "2":
            user = _handle_register(input_function, repository_bundle)
        elif choice == "3":
            return 0
        else:
            print("Invalid option. Please choose 1, 2, or 3.")
            continue

        if user is not None and _run_action_loop(input_function, repository_bundle, user):
            return 0


def _handle_login(input_function: InputFunction, repository_bundle: RepositoryBundle) -> User | None:
    username = _prompt_required(input_function, "Username: ")
    password = _prompt_required(input_function, "Password: ")

    authentication_service = UserAuthenticationService(repository_bundle.user_repository)
    try:
        user = authentication_service.login(username, password)
    except SocialPlatformError as error:
        print(f"Error: {error}")
        return None

    print(f"Welcome back, {user.display_name}!")
    return user


def _handle_register(input_function: InputFunction, repository_bundle: RepositoryBundle) -> User | None:
    username = _prompt_required(input_function, "Choose a username (3-30 letters/digits/_): ")
    email = _prompt_required(input_function, "Email: ")
    password = _prompt_required(
        input_function,
        "Choose a password (8+ chars, upper, lower, digit, special character): ",
    )
    display_name = _prompt_required(input_function, "Display name: ")

    registration_service = UserRegistrationService(repository_bundle.user_repository)
    try:
        user = registration_service.register_user(username, email, password, display_name)
    except SocialPlatformError as error:
        print(f"Error: {error}")
        return None

    print(f"Registered user {user.user_id} (@{user.username}). You are now logged in.")
    return user


def _run_action_loop(
    input_function: InputFunction, repository_bundle: RepositoryBundle, user: User
) -> bool:
    """Run the post-login action menu; returns True if the user chose to exit the program."""
    while True:
        print(_ACTION_MENU)
        choice = input_function(f"[{user.username}] Choose an option: ").strip()

        if choice == "1":
            _handle_create_post(input_function, repository_bundle, user)
        elif choice == "2":
            _handle_follow_user(input_function, repository_bundle, user)
        elif choice == "3":
            _handle_unfollow_user(input_function, repository_bundle, user)
        elif choice == "4":
            _handle_add_comment(input_function, repository_bundle, user)
        elif choice == "5":
            _handle_like_post(input_function, repository_bundle, user)
        elif choice == "6":
            _handle_view_feed(input_function, repository_bundle, user)
        elif choice == "7":
            _handle_view_trending(input_function, repository_bundle)
        elif choice == "8":
            print("Logged out.")
            return False
        elif choice == "9":
            return True
        else:
            print("Invalid option. Please choose a number from 1 to 9.")


def _handle_create_post(
    input_function: InputFunction, repository_bundle: RepositoryBundle, user: User
) -> None:
    content = _prompt_required(input_function, "Post content: ")
    tags_input = input_function("Tags (comma-separated, optional): ").strip()
    tags = [tag.strip() for tag in tags_input.split(",") if tag.strip()] or None
    location = input_function("Location (optional): ").strip() or None

    post_creation_service = PostCreationService(
        repository_bundle.post_repository, repository_bundle.activity_log_repository
    )
    try:
        post = post_creation_service.create_post(user.user_id, content, tags, location)
    except SocialPlatformError as error:
        print(f"Error: {error}")
        return
    print(f"Created post {post.post_id}.")


def _handle_follow_user(
    input_function: InputFunction, repository_bundle: RepositoryBundle, user: User
) -> None:
    followee_user_id = _prompt_int(input_function, "User id to follow: ")
    following_service = UserFollowingService(
        repository_bundle.follower_repository, repository_bundle.activity_log_repository
    )
    try:
        result = following_service.follow_user(user.user_id, followee_user_id)
    except SocialPlatformError as error:
        print(f"Error: {error}")
        return
    print(f"Follow result: {result.value}")


def _handle_unfollow_user(
    input_function: InputFunction, repository_bundle: RepositoryBundle, user: User
) -> None:
    followee_user_id = _prompt_int(input_function, "User id to unfollow: ")
    following_service = UserFollowingService(
        repository_bundle.follower_repository, repository_bundle.activity_log_repository
    )
    try:
        result = following_service.unfollow_user(user.user_id, followee_user_id)
    except SocialPlatformError as error:
        print(f"Error: {error}")
        return
    print(f"Unfollow result: {result.value}")


def _handle_add_comment(
    input_function: InputFunction, repository_bundle: RepositoryBundle, user: User
) -> None:
    post_id = _prompt_int(input_function, "Post id to comment on: ")
    content = _prompt_required(input_function, "Comment: ")

    comment_creation_service = CommentCreationService(
        repository_bundle.comment_repository, repository_bundle.activity_log_repository
    )
    try:
        comment = comment_creation_service.create_comment(post_id, user.user_id, content)
    except SocialPlatformError as error:
        print(f"Error: {error}")
        return
    print(f"Created comment {comment.comment_id}.")


def _handle_like_post(
    input_function: InputFunction, repository_bundle: RepositoryBundle, user: User
) -> None:
    post_id = _prompt_int(input_function, "Post id to like: ")

    engagement_service = PostEngagementService(
        repository_bundle.post_repository, repository_bundle.activity_log_repository
    )
    try:
        engagement_service.like_post(user.user_id, post_id)
    except SocialPlatformError as error:
        print(f"Error: {error}")
        return
    print("Post liked.")


def _handle_view_feed(
    input_function: InputFunction, repository_bundle: RepositoryBundle, user: User
) -> None:
    page = _prompt_int(input_function, "Page number (default 1): ", default=1)

    feed_service = UserTimelineFeedService(
        repository_bundle.post_repository, repository_bundle.timeline_cache_repository
    )
    feed_page = feed_service.get_user_feed_page(user.user_id, page)
    if not feed_page:
        print("No posts to show.")
        return
    for entry in feed_page:
        _print_feed_entry(entry)


def _handle_view_trending(input_function: InputFunction, repository_bundle: RepositoryBundle) -> None:
    since_hours = _prompt_int(
        input_function, "Show posts from the last N hours (default 24): ", default=24
    )
    limit = _prompt_int(input_function, "Max results (default 10): ", default=10)

    trending_service = TrendingPostsService(repository_bundle.post_repository)
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
