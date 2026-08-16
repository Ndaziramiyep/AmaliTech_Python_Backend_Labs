"""Unit tests for the scriptable CLI: one argparse subcommand per user action."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture

from social_platform.cli.app_context import AppContext
from social_platform.cli.commands import main
from social_platform.features.followers.model import FollowResult
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


def _build_fake_context(**overrides: object) -> AppContext:
    defaults: dict[str, object] = {
        "connection_pool": MagicMock(),
        "user_repository": FakeUserRepository(),
        "post_repository": FakePostRepository(),
        "comment_repository": FakeCommentRepository(),
        "follower_repository": FakeFollowerRepository(),
        "feed_repository": FakeFeedRepository(),
        "trending_repository": FakeTrendingRepository(),
        "timeline_cache": FakeTimelineCache(),
        "activity_log_repository": FakeActivityLogRepository(),
    }
    defaults.update(overrides)
    return AppContext(**defaults)  # type: ignore[arg-type]


def _patch_context(mocker: MockerFixture, context: AppContext) -> None:
    mocker.patch("social_platform.cli.commands.build_app_context", return_value=context)


def test_register_user_prints_the_new_user_and_returns_zero(
    mocker: MockerFixture, capsys: pytest.CaptureFixture[str]
) -> None:
    """A successful registration prints the new user's id and username."""
    _patch_context(mocker, _build_fake_context())

    exit_code = main(["register-user", "ada", "ada@example.com", "Super-secret1", "Ada Lovelace"])

    assert exit_code == 0
    assert "Registered user 1 (@ada)" in capsys.readouterr().out


def test_follow_user_prints_the_follow_result_and_returns_zero(
    mocker: MockerFixture, capsys: pytest.CaptureFixture[str]
) -> None:
    """A successful follow prints the outcome and exits 0."""
    follower_repository = FakeFollowerRepository()
    follower_repository.follow_result_to_return = FollowResult.CREATED
    _patch_context(mocker, _build_fake_context(follower_repository=follower_repository))

    exit_code = main(["follow-user", "1", "2"])

    assert exit_code == 0
    assert "created" in capsys.readouterr().out


def test_follow_user_reports_domain_errors_on_stderr_and_returns_one(
    mocker: MockerFixture, capsys: pytest.CaptureFixture[str]
) -> None:
    """A self-follow attempt is reported as a clean error, not a traceback."""
    _patch_context(mocker, _build_fake_context())

    exit_code = main(["follow-user", "1", "1"])

    assert exit_code == 1
    assert "cannot follow themselves" in capsys.readouterr().err


def test_unfollow_user_prints_the_unfollow_result(
    mocker: MockerFixture, capsys: pytest.CaptureFixture[str]
) -> None:
    """A successful unfollow prints the outcome."""
    _patch_context(mocker, _build_fake_context())

    exit_code = main(["unfollow-user", "1", "2"])

    assert exit_code == 0
    assert "Unfollow result:" in capsys.readouterr().out


def test_create_post_prints_the_new_post_id(
    mocker: MockerFixture, capsys: pytest.CaptureFixture[str]
) -> None:
    """Creating a post prints its id, and --tag/--location become JSONB metadata."""
    _patch_context(mocker, _build_fake_context())

    exit_code = main(["create-post", "1", "hello world", "--tag", "python", "--location", "Kigali"])

    assert exit_code == 0
    assert "Created post 1." in capsys.readouterr().out


def test_add_comment_prints_the_new_comment_id(
    mocker: MockerFixture, capsys: pytest.CaptureFixture[str]
) -> None:
    """Adding a comment prints its id."""
    _patch_context(mocker, _build_fake_context())

    exit_code = main(["add-comment", "10", "1", "nice post"])

    assert exit_code == 0
    assert "Created comment 1." in capsys.readouterr().out


def test_like_post_reports_a_missing_post_as_a_clean_error(
    mocker: MockerFixture, capsys: pytest.CaptureFixture[str]
) -> None:
    """Liking a nonexistent post is reported as a domain error, not a traceback."""
    _patch_context(mocker, _build_fake_context())

    exit_code = main(["like-post", "1", "999"])

    assert exit_code == 1
    assert "No post with id" in capsys.readouterr().err


def test_get_user_feed_prints_no_posts_message_when_the_feed_is_empty(
    mocker: MockerFixture, capsys: pytest.CaptureFixture[str]
) -> None:
    """An empty feed prints a friendly message instead of nothing at all."""
    _patch_context(mocker, _build_fake_context())

    exit_code = main(["get-user-feed", "1"])

    assert exit_code == 0
    assert "No posts to show." in capsys.readouterr().out


def test_get_trending_posts_prints_no_trending_message_when_there_are_none(
    mocker: MockerFixture, capsys: pytest.CaptureFixture[str]
) -> None:
    """No trending posts prints a friendly message instead of nothing at all."""
    _patch_context(mocker, _build_fake_context())

    exit_code = main(["get-trending-posts"])

    assert exit_code == 0
    assert "No trending posts to show." in capsys.readouterr().out


def test_every_command_closes_the_connection_pool_even_on_error(mocker: MockerFixture) -> None:
    """The connection pool is released whether the command succeeds or raises."""
    context = _build_fake_context()
    _patch_context(mocker, context)

    main(["follow-user", "1", "1"])  # a self-follow, which raises

    context.connection_pool.close_all_connections.assert_called_once_with()  # type: ignore[attr-defined]


def test_no_subcommand_prints_help_and_returns_one(capsys: pytest.CaptureFixture[str]) -> None:
    """Running with no subcommand at all prints usage and exits nonzero."""
    exit_code = main([])

    assert exit_code == 1
    assert "usage:" in capsys.readouterr().out.lower()


def test_an_unknown_subcommand_exits_via_argparse() -> None:
    """An unrecognized subcommand is rejected by argparse itself."""
    with pytest.raises(SystemExit):
        main(["not-a-real-command"])
