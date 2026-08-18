"""Unit tests for the interactive, menu-driven CLI session."""

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
from tests.unit.services._fakes import (
    FakeActivityLogRepository,
    FakeCommentRepository,
    FakeFeedRepository,
    FakeFollowerRepository,
    FakePostRepository,
    FakeTimelineCache,
    FakeTrendingRepository,
    FakeUserRepository,
)


class _ScriptedInput:
    """A stand-in for `input()` that replays canned responses, then raises EOFError."""

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
    follower_repository: FakeFollowerRepository | None = None,
    comment_repository: FakeCommentRepository | None = None,
    feed_repository: FakeFeedRepository | None = None,
    activity_log_repository: FakeActivityLogRepository | None = None,
    connection_pool: MagicMock | None = None,
) -> AppContext:
    return AppContext(
        user_repository=user_repository or FakeUserRepository(),
        post_repository=post_repository or FakePostRepository(),
        comment_repository=comment_repository or FakeCommentRepository(),
        follower_repository=follower_repository or FakeFollowerRepository(),
        feed_repository=feed_repository or FakeFeedRepository(),
        trending_repository=FakeTrendingRepository(),
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
        ["2", "ada", "ada@example.com", "Super-secret1", "Super-secret1", "9"]
    )

    exit_code = run_interactive_session(scripted_input, lambda: context)

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Registered user 1 (@ada)" in output
    assert "You are now logged in." in output
    connection_pool.close_all_connections.assert_called_once_with()


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
            "9",
        ]
    )

    exit_code = run_interactive_session(scripted_input, lambda: context)

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

    exit_code = run_interactive_session(scripted_input, lambda: context)

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

    exit_code = run_interactive_session(scripted_input, lambda: context)

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
            "1",
            "hello world",
            "",
            "",
            "9",
        ]
    )

    exit_code = run_interactive_session(scripted_input, lambda: context)

    assert exit_code == 0
    assert "Created post 1." in capsys.readouterr().out
    ((created_post,),) = [(p,) for p in post_repository.posts_by_id.values()]
    assert created_post.author_user_id == 1
    assert created_post.content == "hello world"


def test_follow_user_uses_the_logged_in_user_as_the_follower() -> None:
    """Following a user never asks for a follower id; it uses the session's user."""
    follower_repository = FakeFollowerRepository()
    context = _build_fake_context(follower_repository=follower_repository)
    scripted_input = _ScriptedInput(
        ["2", "ada", "ada@example.com", "Super-secret1", "Super-secret1", "2", "7", "9"]
    )

    exit_code = run_interactive_session(scripted_input, lambda: context)

    assert exit_code == 0
    assert follower_repository.create_calls == [(1, 7)]


def test_view_feed_reports_no_posts_when_the_feed_is_empty(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """An empty feed page prints a friendly message instead of nothing."""
    context = _build_fake_context()
    scripted_input = _ScriptedInput(
        ["2", "ada", "ada@example.com", "Super-secret1", "Super-secret1", "6", "", "9"]
    )

    exit_code = run_interactive_session(scripted_input, lambda: context)

    assert exit_code == 0
    assert "No posts to show." in capsys.readouterr().out


def test_add_comment_lists_feed_posts_and_comments_on_the_chosen_one(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Commenting shows the user's feed as a numbered list instead of asking for a raw post id."""
    feed_repository = FakeFeedRepository()
    feed_repository.feed_page_to_return = [
        FeedPostEntry(42, 7, "grace", "hello from grace", {}, datetime.now()),
        FeedPostEntry(43, 8, "linus", "hello from linus", {}, datetime.now()),
    ]
    comment_repository = FakeCommentRepository()
    context = _build_fake_context(
        feed_repository=feed_repository, comment_repository=comment_repository
    )
    scripted_input = _ScriptedInput(
        [
            "2",
            "ada",
            "ada@example.com",
            "Super-secret1",
            "Super-secret1",
            "4",
            "2",
            "nice one",
            "9",
        ]
    )

    exit_code = run_interactive_session(scripted_input, lambda: context)

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "1. @grace: hello from grace" in output
    assert "2. @linus: hello from linus" in output
    assert "Created comment 1." in output


def test_like_post_lists_feed_posts_and_likes_the_chosen_one() -> None:
    """Liking shows the user's feed as a numbered list instead of asking for a raw post id."""
    feed_repository = FakeFeedRepository()
    feed_repository.feed_page_to_return = [
        FeedPostEntry(42, 7, "grace", "hello from grace", {}, datetime.now()),
    ]
    post_repository = FakePostRepository()
    post_repository.posts_by_id[42] = Post(42, 7, "hello from grace", {}, datetime.now())
    activity_log_repository = FakeActivityLogRepository()
    context = _build_fake_context(
        post_repository=post_repository,
        feed_repository=feed_repository,
        activity_log_repository=activity_log_repository,
    )
    scripted_input = _ScriptedInput(
        ["2", "ada", "ada@example.com", "Super-secret1", "Super-secret1", "5", "1", "9"]
    )

    exit_code = run_interactive_session(scripted_input, lambda: context)

    assert exit_code == 0
    assert activity_log_repository.recorded_events[-1].target_post_id == 42


def test_add_comment_with_an_empty_feed_reports_no_posts_available(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """With an empty feed, commenting is refused with a friendly message, not a raw id prompt."""
    context = _build_fake_context()
    scripted_input = _ScriptedInput(
        ["2", "ada", "ada@example.com", "Super-secret1", "Super-secret1", "4", "9"]
    )

    exit_code = run_interactive_session(scripted_input, lambda: context)

    assert exit_code == 0
    assert "No posts available to comment on yet. Follow someone first." in capsys.readouterr().out


def test_running_out_of_input_exits_cleanly_and_closes_the_connection_pool() -> None:
    """Piped input hitting EOF ends the session with a zero exit code, not a crash."""
    connection_pool = MagicMock()
    context = _build_fake_context(connection_pool=connection_pool)
    scripted_input = _ScriptedInput([])

    exit_code = run_interactive_session(scripted_input, lambda: context)

    assert exit_code == 0
    connection_pool.close_all_connections.assert_called_once_with()
