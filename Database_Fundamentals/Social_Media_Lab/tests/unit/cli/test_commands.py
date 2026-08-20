"""Unit tests for the scriptable CLI: one argparse subcommand per user action."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture

from social_platform.cli.app_context import AppContext
from social_platform.cli.commands import main
from social_platform.features.followers.model import FollowResult
from social_platform.features.likes.model import LikeResult, UnlikeResult
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


def _build_fake_context(**overrides: object) -> AppContext:
    defaults: dict[str, object] = {
        "connection_pool": MagicMock(),
        "user_repository": FakeUserRepository(),
        "post_repository": FakePostRepository(),
        "tag_repository": FakeTagRepository(),
        "comment_repository": FakeCommentRepository(),
        "follower_repository": FakeFollowerRepository(),
        "like_repository": FakeLikeRepository(),
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

    exit_code = main(["register-user", "ada", "ada@example.com", "Super-secret1"])

    assert exit_code == 0
    assert "Registered user 1 (@ada)" in capsys.readouterr().out


def test_register_user_accepts_an_optional_bio(
    mocker: MockerFixture, capsys: pytest.CaptureFixture[str]
) -> None:
    """The --bio flag is stored on the new user."""
    user_repository = FakeUserRepository()
    _patch_context(mocker, _build_fake_context(user_repository=user_repository))

    exit_code = main(
        ["register-user", "ada", "ada@example.com", "Super-secret1", "--bio", "Mathematician."]
    )

    assert exit_code == 0
    assert user_repository.users_by_id[1].bio == "Mathematician."


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


def test_update_post_rejects_a_non_owner(
    mocker: MockerFixture, capsys: pytest.CaptureFixture[str]
) -> None:
    """Editing someone else's post is reported as a clean ownership error."""
    post_repository = FakePostRepository()
    post_repository.create_post(1, "original", {})
    _patch_context(mocker, _build_fake_context(post_repository=post_repository))

    exit_code = main(["update-post", "1", "999", "hijacked"])

    assert exit_code == 1
    assert "does not own" in capsys.readouterr().err


def test_update_post_by_the_owner_succeeds(
    mocker: MockerFixture, capsys: pytest.CaptureFixture[str]
) -> None:
    """The author can update their own post."""
    post_repository = FakePostRepository()
    post_repository.create_post(1, "original", {})
    _patch_context(mocker, _build_fake_context(post_repository=post_repository))

    exit_code = main(["update-post", "1", "1", "updated"])

    assert exit_code == 0
    assert "Updated post 1." in capsys.readouterr().out
    assert post_repository.posts_by_id[1].content == "updated"


def test_delete_post_by_the_owner_succeeds(
    mocker: MockerFixture, capsys: pytest.CaptureFixture[str]
) -> None:
    """The author can delete their own post."""
    post_repository = FakePostRepository()
    post_repository.create_post(1, "goodbye", {})
    _patch_context(mocker, _build_fake_context(post_repository=post_repository))

    exit_code = main(["delete-post", "1", "1"])

    assert exit_code == 0
    assert "Deleted post 1." in capsys.readouterr().out
    assert post_repository.find_post_by_id(1) is None


def test_add_comment_prints_the_new_comment_id(
    mocker: MockerFixture, capsys: pytest.CaptureFixture[str]
) -> None:
    """Adding a comment prints its id."""
    _patch_context(mocker, _build_fake_context())

    exit_code = main(["add-comment", "10", "1", "nice post"])

    assert exit_code == 0
    assert "Created comment 1." in capsys.readouterr().out


def test_delete_comment_by_the_owner_succeeds(
    mocker: MockerFixture, capsys: pytest.CaptureFixture[str]
) -> None:
    """The commenter can delete their own comment."""
    comment_repository = FakeCommentRepository()
    comment_repository.create_comment(10, 1, "nice post")
    _patch_context(mocker, _build_fake_context(comment_repository=comment_repository))

    exit_code = main(["delete-comment", "1", "1"])

    assert exit_code == 0
    assert "Deleted comment 1." in capsys.readouterr().out
    assert comment_repository.find_comment_by_id(1) is None


def test_delete_comment_rejects_a_non_owner(
    mocker: MockerFixture, capsys: pytest.CaptureFixture[str]
) -> None:
    """Deleting someone else's comment is reported as a clean ownership error."""
    comment_repository = FakeCommentRepository()
    comment_repository.create_comment(10, 1, "nice post")
    _patch_context(mocker, _build_fake_context(comment_repository=comment_repository))

    exit_code = main(["delete-comment", "1", "999"])

    assert exit_code == 1
    assert "does not own" in capsys.readouterr().err


def test_like_post_reports_a_missing_post_as_a_clean_error(
    mocker: MockerFixture, capsys: pytest.CaptureFixture[str]
) -> None:
    """Liking a nonexistent post is reported as a domain error, not a traceback."""
    _patch_context(mocker, _build_fake_context())

    exit_code = main(["like-post", "1", "999"])

    assert exit_code == 1
    assert "No post with id" in capsys.readouterr().err


def test_like_post_prints_post_liked_on_a_fresh_like(
    mocker: MockerFixture, capsys: pytest.CaptureFixture[str]
) -> None:
    """A first-time like prints the success message."""
    post_repository = FakePostRepository()
    post_repository.create_post(2, "hello", {})  # id 1, the FakePostRepository's first post
    like_repository = FakeLikeRepository()
    like_repository.like_result_to_return = LikeResult.CREATED
    _patch_context(
        mocker,
        _build_fake_context(post_repository=post_repository, like_repository=like_repository),
    )

    exit_code = main(["like-post", "1", "1"])

    assert exit_code == 0
    assert "Post liked." in capsys.readouterr().out


def test_like_post_reports_already_liked_on_a_repeat_like(
    mocker: MockerFixture, capsys: pytest.CaptureFixture[str]
) -> None:
    """Liking the same post twice is idempotent, not an error."""
    post_repository = FakePostRepository()
    post_repository.create_post(2, "hello", {})  # id 1, the FakePostRepository's first post
    like_repository = FakeLikeRepository()
    like_repository.like_result_to_return = LikeResult.ALREADY_EXISTS
    _patch_context(
        mocker,
        _build_fake_context(post_repository=post_repository, like_repository=like_repository),
    )

    exit_code = main(["like-post", "1", "1"])

    assert exit_code == 0
    assert "You already liked this post." in capsys.readouterr().out


def test_unlike_post_prints_like_removed_on_success(
    mocker: MockerFixture, capsys: pytest.CaptureFixture[str]
) -> None:
    """Removing an actual like prints the success message."""
    like_repository = FakeLikeRepository()
    like_repository.unlike_result_to_return = UnlikeResult.REMOVED
    _patch_context(mocker, _build_fake_context(like_repository=like_repository))

    exit_code = main(["unlike-post", "1", "1"])

    assert exit_code == 0
    assert "Like removed." in capsys.readouterr().out


def test_unlike_post_reports_it_was_not_liked(
    mocker: MockerFixture, capsys: pytest.CaptureFixture[str]
) -> None:
    """Unliking a post you never liked is idempotent, not an error."""
    like_repository = FakeLikeRepository()
    like_repository.unlike_result_to_return = UnlikeResult.DID_NOT_EXIST
    _patch_context(mocker, _build_fake_context(like_repository=like_repository))

    exit_code = main(["unlike-post", "1", "1"])

    assert exit_code == 0
    assert "You hadn't liked this post." in capsys.readouterr().out


def test_get_user_profile_prints_bio_and_counts(
    mocker: MockerFixture, capsys: pytest.CaptureFixture[str]
) -> None:
    """A successful profile lookup prints the username, bio, and activity counts."""
    user_repository = FakeUserRepository()
    user_repository.create_user("ada", "ada@example.com", "hash", "Mathematician.")
    _patch_context(mocker, _build_fake_context(user_repository=user_repository))

    exit_code = main(["get-user-profile", "ada"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "@ada" in output
    assert "Mathematician." in output
    assert "0 posts | 0 followers | 0 following" in output


def test_get_user_profile_reports_a_missing_username_as_a_clean_error(
    mocker: MockerFixture, capsys: pytest.CaptureFixture[str]
) -> None:
    """Looking up a nonexistent username is a clean domain error, not a traceback."""
    _patch_context(mocker, _build_fake_context())

    exit_code = main(["get-user-profile", "nobody"])

    assert exit_code == 1
    assert "No user with username" in capsys.readouterr().err


def test_update_bio_prints_confirmation(
    mocker: MockerFixture, capsys: pytest.CaptureFixture[str]
) -> None:
    """A successful bio update prints a confirmation naming the user."""
    user_repository = FakeUserRepository()
    user_repository.create_user("ada", "ada@example.com", "hash")
    _patch_context(mocker, _build_fake_context(user_repository=user_repository))

    exit_code = main(["update-bio", "1", "New bio."])

    assert exit_code == 0
    assert "Updated bio for @ada." in capsys.readouterr().out
    assert user_repository.users_by_id[1].bio == "New bio."


def test_search_users_prints_no_users_message_when_there_are_no_matches(
    mocker: MockerFixture, capsys: pytest.CaptureFixture[str]
) -> None:
    """A query matching nobody prints a friendly message instead of nothing at all."""
    _patch_context(mocker, _build_fake_context())

    exit_code = main(["search-users", "nonexistent"])

    assert exit_code == 0
    assert "No users found." in capsys.readouterr().out


def test_search_users_prints_matching_usernames(
    mocker: MockerFixture, capsys: pytest.CaptureFixture[str]
) -> None:
    """A query matching a username prints it."""
    user_repository = FakeUserRepository()
    user_repository.create_user("grace", "grace@example.com", "hash")
    _patch_context(mocker, _build_fake_context(user_repository=user_repository))

    exit_code = main(["search-users", "gra"])

    assert exit_code == 0
    assert "@grace" in capsys.readouterr().out


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
