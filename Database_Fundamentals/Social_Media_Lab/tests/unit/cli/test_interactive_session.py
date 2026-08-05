"""Unit tests for the interactive, menu-driven CLI session."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime
from unittest.mock import MagicMock

import pytest

from social_platform.cli._composition import RepositoryBundle
from social_platform.cli.interactive_session import run_interactive_session
from social_platform.models.entities import FeedPostEntry, Post
from social_platform.security.password_hashing import hash_password
from tests.unit.services._fakes import (
    FakeActivityLogRepository,
    FakeCommentRepository,
    FakeFollowerRepository,
    FakePostRepository,
    FakeTimelineCacheRepository,
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


def _build_fake_bundle(
    user_repository: FakeUserRepository | None = None,
    post_repository: FakePostRepository | None = None,
    follower_repository: FakeFollowerRepository | None = None,
    comment_repository: FakeCommentRepository | None = None,
) -> RepositoryBundle:
    return RepositoryBundle(
        user_repository=user_repository or FakeUserRepository(),
        post_repository=post_repository or FakePostRepository(),
        comment_repository=comment_repository or FakeCommentRepository(),
        follower_repository=follower_repository or FakeFollowerRepository(),
        timeline_cache_repository=FakeTimelineCacheRepository(),
        activity_log_repository=FakeActivityLogRepository(),
        connection_pool=MagicMock(),
    )


def test_register_then_exit_logs_the_new_user_in_and_closes_the_connection_pool(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Registering lands the user on the action menu already logged in."""
    bundle = _build_fake_bundle()
    scripted_input = _ScriptedInput(
        ["2", "ada", "ada@example.com", "Super-secret1", "Ada Lovelace", "9"]
    )

    exit_code = run_interactive_session(scripted_input, lambda: bundle)

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Registered user 1 (@ada)" in output
    assert "You are now logged in." in output
    bundle.connection_pool.close_all_connections.assert_called_once_with()


def test_register_with_a_weak_password_reports_the_error_and_allows_retry(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A weak password is rejected with a clear message, without abandoning the session."""
    bundle = _build_fake_bundle()
    scripted_input = _ScriptedInput(
        [
            "2",
            "ada",
            "ada@example.com",
            "weak",
            "Ada Lovelace",
            "3",
        ]
    )

    exit_code = run_interactive_session(scripted_input, lambda: bundle)

    assert exit_code == 0
    assert "Password must contain" in capsys.readouterr().out


def test_login_with_the_wrong_password_returns_to_the_guest_menu(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A failed login reports the error and lets the user try again or exit."""
    user_repository = FakeUserRepository()
    user_repository.users_by_id[1] = MagicMock(username="ada")
    user_repository.password_hashes_by_username["ada"] = hash_password("super-secret")
    bundle = _build_fake_bundle(user_repository=user_repository)
    scripted_input = _ScriptedInput(["1", "ada", "wrong-password", "3"])

    exit_code = run_interactive_session(scripted_input, lambda: bundle)

    assert exit_code == 0
    assert "Invalid username or password" in capsys.readouterr().out


def test_create_post_uses_the_logged_in_user_as_the_author(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Creating a post never asks for an author id; it uses the session's user."""
    post_repository = FakePostRepository()
    bundle = _build_fake_bundle(post_repository=post_repository)
    scripted_input = _ScriptedInput(
        [
            "2",
            "ada",
            "ada@example.com",
            "Super-secret1",
            "Ada Lovelace",
            "1",
            "hello world",
            "",
            "",
            "9",
        ]
    )

    exit_code = run_interactive_session(scripted_input, lambda: bundle)

    assert exit_code == 0
    assert "Created post 1." in capsys.readouterr().out
    ((created_post,),) = [(p,) for p in post_repository.posts_by_id.values()]
    assert created_post.author_user_id == 1
    assert created_post.content == "hello world"


def test_follow_user_uses_the_logged_in_user_as_the_follower() -> None:
    """Following a user never asks for a follower id; it uses the session's user."""
    follower_repository = FakeFollowerRepository()
    bundle = _build_fake_bundle(follower_repository=follower_repository)
    scripted_input = _ScriptedInput(
        ["2", "ada", "ada@example.com", "Super-secret1", "Ada Lovelace", "2", "7", "9"]
    )

    exit_code = run_interactive_session(scripted_input, lambda: bundle)

    assert exit_code == 0
    assert follower_repository.create_calls == [(1, 7)]


def test_view_feed_reports_no_posts_when_the_feed_is_empty(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """An empty feed page prints a friendly message instead of nothing."""
    bundle = _build_fake_bundle()
    scripted_input = _ScriptedInput(
        ["2", "ada", "ada@example.com", "Super-secret1", "Ada Lovelace", "6", "", "9"]
    )

    exit_code = run_interactive_session(scripted_input, lambda: bundle)

    assert exit_code == 0
    assert "No posts to show." in capsys.readouterr().out


def test_add_comment_lists_feed_posts_and_comments_on_the_chosen_one(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Commenting shows the user's feed as a numbered list instead of asking for a raw post id."""
    post_repository = FakePostRepository()
    post_repository.feed_page_to_return = [
        FeedPostEntry(42, 7, "grace", "hello from grace", {}, datetime.now()),
        FeedPostEntry(43, 8, "linus", "hello from linus", {}, datetime.now()),
    ]
    comment_repository = FakeCommentRepository()
    bundle = _build_fake_bundle(
        post_repository=post_repository, comment_repository=comment_repository
    )
    scripted_input = _ScriptedInput(
        ["2", "ada", "ada@example.com", "Super-secret1", "Ada Lovelace", "4", "2", "nice one", "9"]
    )

    exit_code = run_interactive_session(scripted_input, lambda: bundle)

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "1. @grace: hello from grace" in output
    assert "2. @linus: hello from linus" in output
    assert "Created comment 1." in output


def test_like_post_lists_feed_posts_and_likes_the_chosen_one() -> None:
    """Liking shows the user's feed as a numbered list instead of asking for a raw post id."""
    post_repository = FakePostRepository()
    post_repository.feed_page_to_return = [
        FeedPostEntry(42, 7, "grace", "hello from grace", {}, datetime.now()),
    ]
    post_repository.posts_by_id[42] = Post(42, 7, "hello from grace", {}, datetime.now())
    activity_log_repository = FakeActivityLogRepository()
    bundle = RepositoryBundle(
        user_repository=FakeUserRepository(),
        post_repository=post_repository,
        comment_repository=FakeCommentRepository(),
        follower_repository=FakeFollowerRepository(),
        timeline_cache_repository=FakeTimelineCacheRepository(),
        activity_log_repository=activity_log_repository,
        connection_pool=MagicMock(),
    )
    scripted_input = _ScriptedInput(
        ["2", "ada", "ada@example.com", "Super-secret1", "Ada Lovelace", "5", "1", "9"]
    )

    exit_code = run_interactive_session(scripted_input, lambda: bundle)

    assert exit_code == 0
    assert activity_log_repository.recorded_events[-1].target_post_id == 42


def test_add_comment_with_an_empty_feed_reports_no_posts_available(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """With an empty feed, commenting is refused with a friendly message, not a raw id prompt."""
    bundle = _build_fake_bundle()
    scripted_input = _ScriptedInput(
        ["2", "ada", "ada@example.com", "Super-secret1", "Ada Lovelace", "4", "9"]
    )

    exit_code = run_interactive_session(scripted_input, lambda: bundle)

    assert exit_code == 0
    assert "No posts available to comment on yet. Follow someone first." in capsys.readouterr().out


def test_running_out_of_input_exits_cleanly_and_closes_the_connection_pool() -> None:
    """Piped input hitting EOF ends the session with a zero exit code, not a crash."""
    bundle = _build_fake_bundle()
    scripted_input = _ScriptedInput([])

    exit_code = run_interactive_session(scripted_input, lambda: bundle)

    assert exit_code == 0
    bundle.connection_pool.close_all_connections.assert_called_once_with()
