"""A menu-driven, interactive front end for the social platform CLI.

Presents a login/register gate, then a short top-level action menu that drills down into
context: browsing a feed leads to a post, a post leads to its comment thread, a search leads
to a user's profile -- so the actor never has to type a raw post/user/comment id, only pick
one from a list of what's actually there.
"""

from __future__ import annotations

import getpass
from collections.abc import Callable
from datetime import UTC, datetime, timedelta

from social_platform.cli.app_context import AppContext, build_app_context
from social_platform.common.exceptions import SocialPlatformError
from social_platform.features.comments.model import CommentThreadEntry
from social_platform.features.comments.service import CommentService
from social_platform.features.feed.service import FeedService
from social_platform.features.followers.service import FollowService
from social_platform.features.likes.service import LikeService
from social_platform.features.posts.model import Post
from social_platform.features.posts.service import PostService
from social_platform.features.profile.model import UserProfile
from social_platform.features.profile.service import ProfileService
from social_platform.features.trending.service import TrendingService
from social_platform.features.users.model import User
from social_platform.features.users.service import UserService

InputFunction = Callable[[str], str]

_GUEST_MENU = """
1. Login
2. Register
3. Exit"""

_ACTION_MENU = """
1. Create a post
2. Browse your feed
3. Browse trending posts
4. Find people
5. My profile
6. Logout
7. Exit"""


def run_interactive_session(
    input_function: InputFunction = input,
    password_input_function: InputFunction = getpass.getpass,
    app_context_factory: Callable[[], AppContext] = build_app_context,
) -> int:
    """Run the menu-driven CLI loop until the user exits or input is exhausted.

    Password entry uses `password_input_function` (real `getpass.getpass` by default),
    which suppresses terminal echo -- separate from `input_function` so ordinary
    prompts still show what's typed. `getpass` needs a real terminal; it falls back to
    a visible `input()`-like prompt (with a warning) when none is attached, e.g. when
    stdin is piped, rather than failing outright.
    """
    context = app_context_factory()
    try:
        return _run_guest_loop(input_function, password_input_function, context)
    except EOFError:
        print()
        return 0
    finally:
        context.connection_pool.close_all_connections()


def _run_guest_loop(
    input_function: InputFunction, password_input_function: InputFunction, context: AppContext
) -> int:
    while True:
        print(_GUEST_MENU)
        choice = input_function("Choose an option: ").strip()

        if choice == "1":
            user = _handle_login(input_function, password_input_function, context)
        elif choice == "2":
            user = _handle_register(input_function, password_input_function, context)
        elif choice == "3":
            return 0
        else:
            print("Invalid option. Please choose 1, 2, or 3.")
            continue

        if user is not None and _run_action_loop(input_function, context, user):
            return 0


def _handle_login(
    input_function: InputFunction, password_input_function: InputFunction, context: AppContext
) -> User | None:
    username = _prompt_required(input_function, "Username: ")
    password = _prompt_required(password_input_function, "Password: ")

    user_service = _build_user_service(context)
    try:
        user = user_service.login(username, password)
    except SocialPlatformError as error:
        print(f"Error: {error}")
        return None

    print(f"Welcome back, @{user.username}!")
    return user


def _handle_register(
    input_function: InputFunction, password_input_function: InputFunction, context: AppContext
) -> User | None:
    username = _prompt_required(input_function, "Choose a username (3-30 letters/digits/_): ")
    email = _prompt_required(input_function, "Email: ")
    password = _prompt_password_with_confirmation(password_input_function)
    bio = input_function("Bio (optional): ").strip() or None

    user_service = _build_user_service(context)
    try:
        user = user_service.register(username, email, password, bio)
    except SocialPlatformError as error:
        print(f"Error: {error}")
        return None

    print(f"Registered user {user.user_id} (@{user.username}). You are now logged in.")
    return user


def _prompt_password_with_confirmation(password_input_function: InputFunction) -> str:
    """Prompt for a password twice (hidden), re-prompting both until the two match."""
    while True:
        password = _prompt_required(
            password_input_function,
            "Choose a password (8+ chars, upper, lower, digit, special character): ",
        )
        confirmation = _prompt_required(password_input_function, "Confirm password: ")
        if password == confirmation:
            return password
        print("Passwords do not match. Please try again.")


def _run_action_loop(input_function: InputFunction, context: AppContext, user: User) -> bool:
    """Run the post-login action menu; returns True if the user chose to exit the program."""
    while True:
        print(_ACTION_MENU)
        choice = input_function(f"[{user.username}] Choose an option: ").strip()

        if choice == "1":
            _handle_create_post(input_function, context, user)
        elif choice == "2":
            _browse_feed(input_function, context, user)
        elif choice == "3":
            _browse_trending(input_function, context, user)
        elif choice == "4":
            _handle_find_people(input_function, context, user)
        elif choice == "5":
            _handle_my_profile(input_function, context, user)
        elif choice == "6":
            print("Logged out.")
            return False
        elif choice == "7":
            return True
        else:
            print("Invalid option. Please choose a number from 1 to 7.")


def _handle_create_post(input_function: InputFunction, context: AppContext, user: User) -> None:
    content = _prompt_required(input_function, "Post content: ")
    tags_input = input_function("Tags (comma-separated, optional): ").strip()
    tags = [tag.strip() for tag in tags_input.split(",") if tag.strip()] or None
    location = input_function("Location (optional): ").strip() or None

    post_service = _build_post_service(context)
    try:
        post = post_service.create_post(user.user_id, content, tags, location)
    except SocialPlatformError as error:
        print(f"Error: {error}")
        return
    print(f"Created post {post.post_id}.")


def _browse_feed(input_function: InputFunction, context: AppContext, user: User) -> None:
    """List the actor's feed and let them open one post, instead of asking for a post id."""
    page = _prompt_int(input_function, "Page number (default 1): ", default=1)
    feed_service = FeedService(context.feed_repository, context.timeline_cache)
    feed_page = feed_service.get_user_feed_page(user.user_id, page)
    if not feed_page:
        print("No posts to show. Follow someone to see their posts here.")
        return

    print("Your feed:")
    for index, entry in enumerate(feed_page, start=1):
        print(f"{index}. @{entry.author_username}: {entry.content}")

    choice = _prompt_selection(
        input_function, f"Open a post (1-{len(feed_page)}, 0 to go back): ", len(feed_page)
    )
    if choice == 0:
        return
    entry = feed_page[choice - 1]
    _open_post_detail(
        input_function, context, user, entry.post_id, entry.author_user_id, entry.author_username
    )


def _browse_trending(input_function: InputFunction, context: AppContext, user: User) -> None:
    """List trending posts and let the actor open one, instead of asking for a post id."""
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

    print("Trending posts:")
    for index, entry in enumerate(trending_posts, start=1):
        print(f"{index}. ({entry.comment_count} comments) {entry.content}")

    choice = _prompt_selection(
        input_function,
        f"Open a post (1-{len(trending_posts)}, 0 to go back): ",
        len(trending_posts),
    )
    if choice == 0:
        return
    entry = trending_posts[choice - 1]
    _open_post_detail(input_function, context, user, entry.post_id, entry.author_user_id, None)


def _browse_my_posts(input_function: InputFunction, context: AppContext, user: User) -> None:
    """List the actor's own posts and let them open one, instead of asking for a post id."""
    post_service = _build_post_service(context)
    own_posts = post_service.get_posts_by_author(user.user_id)
    if not own_posts:
        print("You have no posts yet.")
        return

    print("Your posts:")
    for index, post in enumerate(own_posts, start=1):
        print(f"{index}. {post.content}")

    choice = _prompt_selection(
        input_function, f"Open a post (1-{len(own_posts)}, 0 to go back): ", len(own_posts)
    )
    if choice == 0:
        return
    post = own_posts[choice - 1]
    _open_post_detail(input_function, context, user, post.post_id, user.user_id, user.username)


def _open_post_detail(
    input_function: InputFunction,
    context: AppContext,
    user: User,
    post_id: int,
    author_user_id: int,
    author_username: str | None,
) -> None:
    """Show one post and everything you can do to it: comment, like/unlike, edit, delete."""
    post_service = _build_post_service(context)
    like_service = _build_like_service(context)
    is_owner = author_user_id == user.user_id

    while True:
        post = post_service.get_post(post_id)
        if post is None:
            print("This post no longer exists.")
            return

        heading = f"@{author_username}" if author_username else f"post {post_id}"
        print(f"\n--- Post by {heading} ---")
        print(post.content)

        already_liked = like_service.has_liked(user.user_id, post_id)
        actions = ["View / add comments", "Unlike this post" if already_liked else "Like this post"]
        if is_owner:
            actions += ["Edit this post", "Delete this post"]
        actions.append("Back")
        selected = _prompt_action(input_function, actions)

        if selected == "View / add comments":
            _open_comment_thread(input_function, context, user, post_id)
        elif selected in ("Like this post", "Unlike this post"):
            _toggle_like(like_service, user, post_id, already_liked)
        elif selected == "Edit this post":
            _handle_edit_post_in_place(input_function, post_service, user, post)
        elif selected == "Delete this post":
            if _handle_delete_post_in_place(post_service, user, post_id):
                return
        else:
            return


def _toggle_like(like_service: LikeService, user: User, post_id: int, already_liked: bool) -> None:
    """Like the post, or remove an existing like -- whichever the current state calls for."""
    if already_liked:
        like_service.unlike_post(user.user_id, post_id)
        print("Like removed.")
        return
    try:
        like_service.like_post(user.user_id, post_id)
    except SocialPlatformError as error:
        print(f"Error: {error}")
    else:
        print("Post liked.")


def _handle_edit_post_in_place(
    input_function: InputFunction, post_service: PostService, user: User, post: Post
) -> None:
    content = _prompt_required(input_function, f"New content (was: {post.content!r}): ")
    location = input_function("New location (optional): ").strip() or None
    try:
        post_service.update_post(post.post_id, user.user_id, content, location)
    except SocialPlatformError as error:
        print(f"Error: {error}")
        return
    print("Post updated.")


def _handle_delete_post_in_place(post_service: PostService, user: User, post_id: int) -> bool:
    """Delete the post; returns True if it was deleted (the detail view should then close)."""
    try:
        post_service.delete_post(post_id, user.user_id)
    except SocialPlatformError as error:
        print(f"Error: {error}")
        return False
    print("Post deleted.")
    return True


def _open_comment_thread(
    input_function: InputFunction, context: AppContext, user: User, post_id: int
) -> None:
    """Show a post's full comment thread and let the actor comment, reply, or delete."""
    comment_service = _build_comment_service(context)

    while True:
        thread = comment_service.get_comment_thread(post_id)
        _print_comment_thread(thread)

        actions = ["Add a new comment"]
        if thread:
            actions += ["Reply to a comment", "Delete one of my comments"]
        actions.append("Back")
        selected = _prompt_action(input_function, actions)

        if selected == "Add a new comment":
            _handle_add_comment(input_function, comment_service, user, post_id)
        elif selected == "Reply to a comment":
            _handle_reply_to_comment(input_function, comment_service, user, post_id, thread)
        elif selected == "Delete one of my comments":
            _handle_delete_comment_from_thread(input_function, comment_service, user, thread)
        else:
            return


def _print_comment_thread(thread: list[CommentThreadEntry]) -> None:
    if not thread:
        print("No comments yet. Be the first to comment.")
        return
    print("Comments:")
    for index, entry in enumerate(thread, start=1):
        print(f"{index}. {'  ' * entry.depth}{entry.comment.content}")


def _handle_add_comment(
    input_function: InputFunction, comment_service: CommentService, user: User, post_id: int
) -> None:
    content = _prompt_required(input_function, "Comment: ")
    try:
        comment_service.create_comment(post_id, user.user_id, content)
    except SocialPlatformError as error:
        print(f"Error: {error}")
    else:
        print("Comment added.")


def _handle_reply_to_comment(
    input_function: InputFunction,
    comment_service: CommentService,
    user: User,
    post_id: int,
    thread: list[CommentThreadEntry],
) -> None:
    reply_choice = _prompt_selection(
        input_function, f"Reply to which comment (1-{len(thread)}, 0 to cancel): ", len(thread)
    )
    if reply_choice == 0:
        return
    parent_comment_id = thread[reply_choice - 1].comment.comment_id
    content = _prompt_required(input_function, "Your reply: ")
    try:
        comment_service.create_comment(post_id, user.user_id, content, parent_comment_id)
    except SocialPlatformError as error:
        print(f"Error: {error}")
    else:
        print("Reply added.")


def _handle_delete_comment_from_thread(
    input_function: InputFunction,
    comment_service: CommentService,
    user: User,
    thread: list[CommentThreadEntry],
) -> None:
    delete_choice = _prompt_selection(
        input_function, f"Delete which comment (1-{len(thread)}, 0 to cancel): ", len(thread)
    )
    if delete_choice == 0:
        return
    comment_id = thread[delete_choice - 1].comment.comment_id
    try:
        comment_service.delete_comment(comment_id, user.user_id)
    except SocialPlatformError as error:
        print(f"Error: {error}")
    else:
        print("Comment deleted.")


def _handle_find_people(input_function: InputFunction, context: AppContext, user: User) -> None:
    """Search for users by username and let the actor open one, instead of asking for an id."""
    user_service = _build_user_service(context)
    query = _prompt_required(input_function, "Search for a username containing: ")
    results = user_service.search_users(query)
    if not results:
        print("No users found.")
        return

    print("Results:")
    for index, result in enumerate(results, start=1):
        print(f"{index}. @{result.username}")

    choice = _prompt_selection(
        input_function, f"Open a user (1-{len(results)}, 0 to go back): ", len(results)
    )
    if choice == 0:
        return
    _open_user_detail(input_function, context, user, results[choice - 1])


def _open_user_detail(
    input_function: InputFunction, context: AppContext, user: User, other_user: User
) -> None:
    """Show another user's profile and let the actor follow/unfollow them."""
    profile_service = _build_profile_service(context)
    follow_service = _build_follow_service(context)
    is_self = other_user.user_id == user.user_id

    while True:
        profile = profile_service.get_profile(other_user.username)
        _print_profile(profile)

        actions = []
        if not is_self:
            already_following = follow_service.is_following(user.user_id, other_user.user_id)
            actions.append("Unfollow" if already_following else "Follow")
        actions.append("Back")
        selected = _prompt_action(input_function, actions)

        if selected == "Follow":
            try:
                follow_service.follow_user(user.user_id, other_user.user_id)
            except SocialPlatformError as error:
                print(f"Error: {error}")
            else:
                print(f"You are now following @{other_user.username}.")
        elif selected == "Unfollow":
            follow_service.unfollow_user(user.user_id, other_user.user_id)
            print(f"You unfollowed @{other_user.username}.")
        else:
            return


def _handle_my_profile(input_function: InputFunction, context: AppContext, user: User) -> None:
    profile_service = _build_profile_service(context)

    while True:
        profile = profile_service.get_profile(user.username)
        _print_profile(profile)

        actions = ["Edit my bio", "My posts", "Back"]
        selected = _prompt_action(input_function, actions)

        if selected == "Edit my bio":
            _handle_edit_bio(input_function, context, user)
        elif selected == "My posts":
            _browse_my_posts(input_function, context, user)
        else:
            return


def _handle_edit_bio(input_function: InputFunction, context: AppContext, user: User) -> None:
    bio = input_function("New bio (leave blank to clear): ").strip() or None
    user_service = _build_user_service(context)
    try:
        user_service.update_bio(user.user_id, bio)
    except SocialPlatformError as error:
        print(f"Error: {error}")
        return
    print("Bio updated.")


def _build_post_service(context: AppContext) -> PostService:
    return PostService(
        context.post_repository, context.tag_repository, context.activity_log_repository
    )


def _build_comment_service(context: AppContext) -> CommentService:
    return CommentService(context.comment_repository, context.activity_log_repository)


def _build_like_service(context: AppContext) -> LikeService:
    return LikeService(
        context.post_repository, context.like_repository, context.activity_log_repository
    )


def _build_follow_service(context: AppContext) -> FollowService:
    return FollowService(context.follower_repository, context.activity_log_repository)


def _build_profile_service(context: AppContext) -> ProfileService:
    return ProfileService(
        context.user_repository, context.post_repository, context.follower_repository
    )


def _build_user_service(context: AppContext) -> UserService:
    return UserService(context.user_repository, context.activity_log_repository)


def _print_profile(profile: UserProfile) -> None:
    print(f"\n@{profile.username}")
    print(profile.bio or "(no bio)")
    print(
        f"{profile.post_count} posts | {profile.follower_count} followers | "
        f"{profile.following_count} following"
    )


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


def _prompt_selection(
    input_function: InputFunction, prompt: str, count: int, allow_zero_for_back: bool = True
) -> int:
    """Prompt for a whole number 1..count, or 0 (meaning "back"/"cancel") if allowed."""
    lowest = 0 if allow_zero_for_back else 1
    while True:
        raw_value = input_function(prompt).strip()
        try:
            value = int(raw_value)
        except ValueError:
            print("Please enter a whole number.")
            continue
        if lowest <= value <= count:
            return value
        print(f"Please enter a number from {lowest} to {count}.")


def _prompt_action(input_function: InputFunction, actions: list[str]) -> str:
    """Print a numbered menu of `actions` and return the one the user picked."""
    for index, action_label in enumerate(actions, start=1):
        print(f"{index}. {action_label}")
    choice = _prompt_selection(
        input_function,
        f"Choose an option (1-{len(actions)}): ",
        len(actions),
        allow_zero_for_back=False,
    )
    return actions[choice - 1]
