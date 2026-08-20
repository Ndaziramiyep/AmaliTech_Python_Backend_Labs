"""Unit tests for the interactive, menu-driven CLI session.

Top-level action-menu numbers used throughout: 1 create post, 2 browse feed, 3 browse
trending, 4 find people, 5 my profile, 6 logout, 7 exit. Everything else (edit/delete a
post, follow/unfollow, comment/reply/delete-comment, like/unlike) is reached by drilling
down from a browsed list, never by typing a raw id -- see the sub-menus each test walks.
"""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime
from unittest.mock import MagicMock

import pytest

from social_platform.cli.app_context import AppContext
from social_platform.cli.interactive import run_interactive_session
from social_platform.common.security import hash_password
from social_platform.features.feed.model import FeedPostEntry
from social_platform.features.posts.model import Post
from social_platform.features.trending.model import TrendingPostEntry
from tests.unit.services._fakes import (
    FakeActivityLogRepository,
    FakeCommentRepository,
    FakeFeedRepository,
    FakeFollowerRepository,
    FakeLikeRepository,
    FakePostRepository,
    FakeTagRepository,
    FakeTimelineCache,
    FakeTrendingRepository,
    FakeUserRepository,
)


class _ScriptedInput:
    """A stand-in for `input()` (or `getpass.getpass`) that replays canned responses,
    then raises EOFError.
    """

    def __init__(self, responses: Iterable[str]) -> None:
        self._responses = iter(responses)

    def __call__(self, prompt: str) -> str:
        try:
            return next(self._responses)
        except StopIteration:
            raise EOFError from None


def _build_fake_context(
    user_repository: FakeUserRepository | None = None,
    post_repository: FakePostRepository | None = None,
    tag_repository: FakeTagRepository | None = None,
    follower_repository: FakeFollowerRepository | None = None,
    like_repository: FakeLikeRepository | None = None,
    comment_repository: FakeCommentRepository | None = None,
    feed_repository: FakeFeedRepository | None = None,
    trending_repository: FakeTrendingRepository | None = None,
    activity_log_repository: FakeActivityLogRepository | None = None,
    connection_pool: MagicMock | None = None,
) -> AppContext:
    return AppContext(
        user_repository=user_repository or FakeUserRepository(),
        post_repository=post_repository or FakePostRepository(),
        tag_repository=tag_repository or FakeTagRepository(),
        comment_repository=comment_repository or FakeCommentRepository(),
        follower_repository=follower_repository or FakeFollowerRepository(),
        like_repository=like_repository or FakeLikeRepository(),
        feed_repository=feed_repository or FakeFeedRepository(),
        trending_repository=trending_repository or FakeTrendingRepository(),
        timeline_cache=FakeTimelineCache(),
        activity_log_repository=activity_log_repository or FakeActivityLogRepository(),
        connection_pool=connection_pool or MagicMock(),
    )


def test_register_then_exit_logs_the_new_user_in_and_closes_the_connection_pool(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Registering lands the user on the action menu already logged in."""
    connection_pool = MagicMock()
    context = _build_fake_context(connection_pool=connection_pool)
    scripted_input = _ScriptedInput(
        ["2", "ada", "ada@example.com", "Super-secret1", "Super-secret1", "", "7"]
    )

    exit_code = run_interactive_session(scripted_input, scripted_input, lambda: context)

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Registered user 1 (@ada)" in output
    assert "You are now logged in." in output
    connection_pool.close_all_connections.assert_called_once_with()


def test_register_prompts_for_an_optional_bio(capsys: pytest.CaptureFixture[str]) -> None:
    """The bio typed at registration is stored on the new user."""
    user_repository = FakeUserRepository()
    context = _build_fake_context(user_repository=user_repository)
    scripted_input = _ScriptedInput(
        ["2", "ada", "ada@example.com", "Super-secret1", "Super-secret1", "Mathematician.", "7"]
    )

    exit_code = run_interactive_session(scripted_input, scripted_input, lambda: context)

    assert exit_code == 0
    assert user_repository.users_by_id[1].bio == "Mathematician."


def test_password_prompts_use_the_dedicated_hidden_input_channel(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Password/confirm-password are read from `password_input_function`, not `input_function`.

    In production, `password_input_function` defaults to `getpass.getpass`, which
    suppresses terminal echo -- proving the two channels are wired separately (rather
    than both happening to read the same shared list) is what actually protects a real
    user's password from being echoed to the terminal.
    """
    ordinary_input = _ScriptedInput(["2", "ada", "ada@example.com", "", "7"])
    password_input = _ScriptedInput(["Super-secret1", "Super-secret1"])

    exit_code = run_interactive_session(
        ordinary_input, password_input, lambda: _build_fake_context()
    )

    assert exit_code == 0
    assert "Registered user 1 (@ada)" in capsys.readouterr().out


def test_register_with_mismatched_passwords_reprompts_until_they_match(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A confirmation that doesn't match the password is rejected, and both are re-asked."""
    context = _build_fake_context()
    scripted_input = _ScriptedInput(
        [
            "2",
            "ada",
            "ada@example.com",
            "Super-secret1",
            "Something-else1",  # mismatched confirmation -> re-prompted
            "Super-secret1",
            "Super-secret1",
            "",
            "7",
        ]
    )

    exit_code = run_interactive_session(scripted_input, scripted_input, lambda: context)

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Passwords do not match. Please try again." in output
    assert "Registered user 1 (@ada)" in output


def test_register_with_a_weak_password_reports_the_error_and_allows_retry(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A weak password is rejected with a clear message, without abandoning the session."""
    context = _build_fake_context()
    scripted_input = _ScriptedInput(["2", "ada", "ada@example.com", "weak", "weak", "3"])

    exit_code = run_interactive_session(scripted_input, scripted_input, lambda: context)

    assert exit_code == 0
    assert "Password must contain" in capsys.readouterr().out


def test_login_with_the_wrong_password_returns_to_the_guest_menu(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A failed login reports the error and lets the user try again or exit."""
    user_repository = FakeUserRepository()
    user_repository.users_by_id[1] = MagicMock(username="ada")
    user_repository.password_hashes_by_username["ada"] = hash_password("super-secret")
    context = _build_fake_context(user_repository=user_repository)
    scripted_input = _ScriptedInput(["1", "ada", "wrong-password", "3"])

    exit_code = run_interactive_session(scripted_input, scripted_input, lambda: context)

    assert exit_code == 0
    assert "Invalid username or password" in capsys.readouterr().out


def test_create_post_uses_the_logged_in_user_as_the_author(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Creating a post never asks for an author id; it uses the session's user."""
    post_repository = FakePostRepository()
    context = _build_fake_context(post_repository=post_repository)
    scripted_input = _ScriptedInput(
        [
            "2",
            "ada",
            "ada@example.com",
            "Super-secret1",
            "Super-secret1",
            "",
            "1",
            "hello world",
            "",
            "",
            "7",
        ]
    )

    exit_code = run_interactive_session(scripted_input, scripted_input, lambda: context)

    assert exit_code == 0
    assert "Created post 1." in capsys.readouterr().out
    ((created_post,),) = [(p,) for p in post_repository.posts_by_id.values()]
    assert created_post.author_user_id == 1
    assert created_post.content == "hello world"


def test_my_posts_lists_and_edits_the_chosen_post(capsys: pytest.CaptureFixture[str]) -> None:
    """My profile -> My posts shows a numbered list, then updates the one chosen from it."""
    post_repository = FakePostRepository()
    post_repository.create_post(1, "original content", {})
    context = _build_fake_context(post_repository=post_repository)
    scripted_input = _ScriptedInput(
        [
            "2",
            "ada",
            "ada@example.com",
            "Super-secret1",
            "Super-secret1",
            "",
            "5",  # My profile
            "2",  # My posts
            "1",  # open post 1
            "3",  # Edit this post
            "updated content",
            "",
            "5",  # Back (post detail)
            "3",  # Back (my profile)
            "7",
        ]
    )

    exit_code = run_interactive_session(scripted_input, scripted_input, lambda: context)

    assert exit_code == 0
    assert "Post updated." in capsys.readouterr().out
    assert post_repository.posts_by_id[1].content == "updated content"


def test_my_posts_lists_and_deletes_the_chosen_post(capsys: pytest.CaptureFixture[str]) -> None:
    """My profile -> My posts shows a numbered list, then removes the one chosen from it."""
    post_repository = FakePostRepository()
    post_repository.create_post(1, "goodbye post", {})
    context = _build_fake_context(post_repository=post_repository)
    scripted_input = _ScriptedInput(
        [
            "2",
            "ada",
            "ada@example.com",
            "Super-secret1",
            "Super-secret1",
            "",
            "5",
            "2",
            "1",
            "4",  # Delete this post
            "3",  # Back (my profile)
            "7",
        ]
    )

    exit_code = run_interactive_session(scripted_input, scripted_input, lambda: context)

    assert exit_code == 0
    assert "Post deleted." in capsys.readouterr().out
    assert post_repository.find_post_by_id(1) is None


def test_my_posts_with_no_posts_reports_nothing_to_open(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """With no posts of your own, My posts reports a friendly message, not a raw id prompt."""
    context = _build_fake_context()
    scripted_input = _ScriptedInput(
        ["2", "ada", "ada@example.com", "Super-secret1", "Super-secret1", "", "5", "2", "3", "7"]
    )

    exit_code = run_interactive_session(scripted_input, scripted_input, lambda: context)

    assert exit_code == 0
    assert "You have no posts yet." in capsys.readouterr().out


def test_find_people_lists_matches_and_follows_the_chosen_user() -> None:
    """Finding people never asks for a user id; it lists matches and follows the one picked."""
    user_repository = FakeUserRepository()
    user_repository.create_user("bob", "bob@example.com", "hash")  # seeded as user id 1
    follower_repository = FakeFollowerRepository()
    context = _build_fake_context(
        user_repository=user_repository, follower_repository=follower_repository
    )
    scripted_input = _ScriptedInput(
        [
            "2",
            "ada",
            "ada@example.com",
            "Super-secret1",
            "Super-secret1",
            "",
            "4",  # Find people
            "bo",  # search query
            "1",  # open the matching user (bob)
            "1",  # Follow
            "2",  # Back
            "7",
        ]
    )

    exit_code = run_interactive_session(scripted_input, scripted_input, lambda: context)

    assert exit_code == 0
    assert follower_repository.create_calls == [(2, 1)]  # ada (id 2) follows bob (id 1)


def test_find_people_with_no_matches_reports_no_users_found(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Searching for a username nobody has is a clean, friendly message, not an error."""
    context = _build_fake_context()
    scripted_input = _ScriptedInput(
        ["2", "ada", "ada@example.com", "Super-secret1", "Super-secret1", "", "4", "nobody", "7"]
    )

    exit_code = run_interactive_session(scripted_input, scripted_input, lambda: context)

    assert exit_code == 0
    assert "No users found." in capsys.readouterr().out


def test_browse_feed_reports_no_posts_when_the_feed_is_empty(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """An empty feed page prints a friendly message instead of nothing."""
    context = _build_fake_context()
    scripted_input = _ScriptedInput(
        ["2", "ada", "ada@example.com", "Super-secret1", "Super-secret1", "", "2", "", "7"]
    )

    exit_code = run_interactive_session(scripted_input, scripted_input, lambda: context)

    assert exit_code == 0
    assert "No posts to show. Follow someone to see their posts here." in capsys.readouterr().out


def test_browse_feed_opens_a_post_and_adds_a_comment(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Browsing the feed lists posts as a numbered menu, then opens the one chosen to comment."""
    feed_repository = FakeFeedRepository()
    feed_repository.feed_page_to_return = [
        FeedPostEntry(42, 7, "grace", "hello from grace", {}, datetime.now()),
        FeedPostEntry(43, 8, "linus", "hello from linus", {}, datetime.now()),
    ]
    post_repository = FakePostRepository()
    post_repository.posts_by_id[42] = Post(42, 7, "hello from grace", {}, datetime.now())
    comment_repository = FakeCommentRepository()
    context = _build_fake_context(
        post_repository=post_repository,
        feed_repository=feed_repository,
        comment_repository=comment_repository,
    )
    scripted_input = _ScriptedInput(
        [
            "2",
            "ada",
            "ada@example.com",
            "Super-secret1",
            "Super-secret1",
            "",
            "2",  # Browse your feed
            "",  # page (default 1)
            "1",  # open post 1 (post 42, grace)
            "1",  # View / add comments (not owner: 3 actions)
            "1",  # Add a new comment (thread empty: 2 actions)
            "nice one",
            "4",  # Back (thread now has 1 entry: 4 actions)
            "3",  # Back (post detail: 3 actions)
            "7",
        ]
    )

    exit_code = run_interactive_session(scripted_input, scripted_input, lambda: context)

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "1. @grace: hello from grace" in output
    assert "2. @linus: hello from linus" in output
    assert "Comment added." in output
    ((comment,),) = [(c,) for c in comment_repository.comments_by_id.values()]
    assert comment.post_id == 42
    assert comment.commenter_user_id == 1
    assert comment.content == "nice one"


def test_comment_thread_supports_replying_to_a_comment(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A reply is linked to its parent comment, forming a threaded sub-comment."""
    post_repository = FakePostRepository()
    post_repository.create_post(1, "my post", {})  # owned by ada (user id 1)
    comment_repository = FakeCommentRepository()
    comment_repository.create_comment(1, 99, "top-level comment")  # comment id 1
    context = _build_fake_context(
        post_repository=post_repository, comment_repository=comment_repository
    )
    scripted_input = _ScriptedInput(
        [
            "2",
            "ada",
            "ada@example.com",
            "Super-secret1",
            "Super-secret1",
            "",
            "5",  # My profile
            "2",  # My posts
            "1",  # open post 1
            "1",  # View / add comments (owner: 5 actions)
            "2",  # Reply to a comment (thread non-empty: 4 actions)
            "1",  # reply to comment 1
            "thanks!",
            "4",  # Back (comment thread)
            "5",  # Back (post detail)
            "3",  # Back (my profile)
            "7",
        ]
    )

    exit_code = run_interactive_session(scripted_input, scripted_input, lambda: context)

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Reply added." in output
    replies = [
        comment
        for comment in comment_repository.comments_by_id.values()
        if comment.parent_comment_id == 1
    ]
    assert len(replies) == 1
    assert replies[0].content == "thanks!"
    assert replies[0].commenter_user_id == 1


def test_comment_thread_deletes_the_chosen_own_comment(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Deleting a comment shows the thread as a numbered list, then removes the one chosen."""
    post_repository = FakePostRepository()
    post_repository.create_post(1, "my post", {})
    comment_repository = FakeCommentRepository()
    comment_repository.create_comment(1, 1, "to delete")  # ada's own comment, id 1
    context = _build_fake_context(
        post_repository=post_repository, comment_repository=comment_repository
    )
    scripted_input = _ScriptedInput(
        [
            "2",
            "ada",
            "ada@example.com",
            "Super-secret1",
            "Super-secret1",
            "",
            "5",
            "2",
            "1",
            "1",  # View / add comments (owner: 5 actions)
            "3",  # Delete one of my comments (thread non-empty: 4 actions)
            "1",  # delete comment 1
            "2",  # Back (thread now empty: 2 actions)
            "5",  # Back (post detail)
            "3",  # Back (my profile)
            "7",
        ]
    )

    exit_code = run_interactive_session(scripted_input, scripted_input, lambda: context)

    assert exit_code == 0
    assert "Comment deleted." in capsys.readouterr().out
    assert comment_repository.find_comment_by_id(1) is None


def test_post_detail_likes_the_chosen_post() -> None:
    """Opening a post from the feed and choosing Like records the like for the session's user."""
    feed_repository = FakeFeedRepository()
    feed_repository.feed_page_to_return = [
        FeedPostEntry(42, 7, "grace", "hello from grace", {}, datetime.now()),
    ]
    post_repository = FakePostRepository()
    post_repository.posts_by_id[42] = Post(42, 7, "hello from grace", {}, datetime.now())
    like_repository = FakeLikeRepository()
    activity_log_repository = FakeActivityLogRepository()
    context = _build_fake_context(
        post_repository=post_repository,
        feed_repository=feed_repository,
        like_repository=like_repository,
        activity_log_repository=activity_log_repository,
    )
    scripted_input = _ScriptedInput(
        [
            "2",
            "ada",
            "ada@example.com",
            "Super-secret1",
            "Super-secret1",
            "",
            "2",
            "",
            "1",
            "2",  # Like this post (not owner: 3 actions)
            "3",  # Back
            "7",
        ]
    )

    exit_code = run_interactive_session(scripted_input, scripted_input, lambda: context)

    assert exit_code == 0
    assert like_repository.create_calls == [(42, 1)]
    assert activity_log_repository.recorded_events[-1].target_post_id == 42


def test_post_detail_shows_unlike_when_already_liked_and_removes_it(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """When the post is already liked, the toggle shows Unlike, which removes the like."""
    feed_repository = FakeFeedRepository()
    feed_repository.feed_page_to_return = [
        FeedPostEntry(42, 7, "grace", "hello from grace", {}, datetime.now()),
    ]
    post_repository = FakePostRepository()
    post_repository.posts_by_id[42] = Post(42, 7, "hello from grace", {}, datetime.now())
    like_repository = FakeLikeRepository()
    like_repository.has_liked_to_return = True
    context = _build_fake_context(
        post_repository=post_repository,
        feed_repository=feed_repository,
        like_repository=like_repository,
    )
    scripted_input = _ScriptedInput(
        [
            "2",
            "ada",
            "ada@example.com",
            "Super-secret1",
            "Super-secret1",
            "",
            "2",
            "",
            "1",
            "2",  # Unlike this post
            "3",  # Back
            "7",
        ]
    )

    exit_code = run_interactive_session(scripted_input, scripted_input, lambda: context)

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "2. Unlike this post" in output
    assert "Like removed." in output
    assert like_repository.delete_calls == [(42, 1)]


def test_browse_trending_opens_a_post(capsys: pytest.CaptureFixture[str]) -> None:
    """Browsing trending posts lists them with their comment count, then opens the one chosen."""
    trending_repository = FakeTrendingRepository()
    trending_repository.trending_posts_to_return = [
        TrendingPostEntry(50, 9, "trending content", {}, datetime.now(), 3),
    ]
    post_repository = FakePostRepository()
    post_repository.posts_by_id[50] = Post(50, 9, "trending content", {}, datetime.now())
    context = _build_fake_context(
        post_repository=post_repository, trending_repository=trending_repository
    )
    scripted_input = _ScriptedInput(
        [
            "2",
            "ada",
            "ada@example.com",
            "Super-secret1",
            "Super-secret1",
            "",
            "3",  # Browse trending posts
            "",  # since_hours default
            "",  # limit default
            "1",  # open post 1
            "3",  # Back (not owner: 3 actions)
            "7",
        ]
    )

    exit_code = run_interactive_session(scripted_input, scripted_input, lambda: context)

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "1. (3 comments) trending content" in output
    assert "--- Post by post 50 ---" in output


def test_my_profile_shows_bio_and_counts(capsys: pytest.CaptureFixture[str]) -> None:
    """My profile shows the bio you registered with plus activity counts."""
    context = _build_fake_context()
    scripted_input = _ScriptedInput(
        [
            "2",
            "ada",
            "ada@example.com",
            "Super-secret1",
            "Super-secret1",
            "Hi there.",
            "5",
            "3",
            "7",
        ]
    )

    exit_code = run_interactive_session(scripted_input, scripted_input, lambda: context)

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "@ada" in output
    assert "Hi there." in output
    assert "0 posts | 0 followers | 0 following" in output


def test_my_profile_edits_the_bio(capsys: pytest.CaptureFixture[str]) -> None:
    """Editing the bio from My profile replaces what's stored for the session's user."""
    user_repository = FakeUserRepository()
    context = _build_fake_context(user_repository=user_repository)
    scripted_input = _ScriptedInput(
        [
            "2",
            "ada",
            "ada@example.com",
            "Super-secret1",
            "Super-secret1",
            "",
            "5",  # My profile
            "1",  # Edit my bio
            "New bio.",
            "3",  # Back
            "7",
        ]
    )

    exit_code = run_interactive_session(scripted_input, scripted_input, lambda: context)

    assert exit_code == 0
    assert "Bio updated." in capsys.readouterr().out
    assert user_repository.users_by_id[1].bio == "New bio."


def test_running_out_of_input_exits_cleanly_and_closes_the_connection_pool() -> None:
    """Piped input hitting EOF ends the session with a zero exit code, not a crash."""
    connection_pool = MagicMock()
    context = _build_fake_context(connection_pool=connection_pool)
    scripted_input = _ScriptedInput([])

    exit_code = run_interactive_session(scripted_input, scripted_input, lambda: context)

    assert exit_code == 0
    connection_pool.close_all_connections.assert_called_once_with()
