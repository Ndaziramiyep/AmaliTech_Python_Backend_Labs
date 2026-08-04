"""Unit tests for the follow-user CLI command's composition root."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture

from social_platform.cli._composition import RepositoryBundle
from social_platform.cli.follow_user_command import main
from social_platform.models.results import FollowResult
from tests.unit.services._fakes import (
    FakeActivityLogRepository,
    FakeCommentRepository,
    FakeFollowerRepository,
    FakePostRepository,
    FakeTimelineCacheRepository,
    FakeUserRepository,
)


def _build_fake_bundle(follower_repository: FakeFollowerRepository) -> RepositoryBundle:
    return RepositoryBundle(
        user_repository=FakeUserRepository(),
        post_repository=FakePostRepository(),
        comment_repository=FakeCommentRepository(),
        follower_repository=follower_repository,
        timeline_cache_repository=FakeTimelineCacheRepository(),
        activity_log_repository=FakeActivityLogRepository(),
        connection_pool=MagicMock(),
    )


def test_main_prints_the_follow_result_and_returns_zero(
    mocker: MockerFixture, capsys: pytest.CaptureFixture[str]
) -> None:
    """A successful follow prints the outcome and exits 0."""
    follower_repository = FakeFollowerRepository()
    follower_repository.follow_result_to_return = FollowResult.CREATED
    mocker.patch(
        "social_platform.cli.follow_user_command.build_repository_bundle",
        return_value=_build_fake_bundle(follower_repository),
    )

    exit_code = main(["1", "2"])

    assert exit_code == 0
    assert "created" in capsys.readouterr().out


def test_main_reports_domain_errors_on_stderr_and_returns_one(
    mocker: MockerFixture, capsys: pytest.CaptureFixture[str]
) -> None:
    """A self-follow attempt is reported as a clean error, not a traceback."""
    follower_repository = FakeFollowerRepository()
    mocker.patch(
        "social_platform.cli.follow_user_command.build_repository_bundle",
        return_value=_build_fake_bundle(follower_repository),
    )

    exit_code = main(["1", "1"])

    assert exit_code == 1
    assert "cannot follow themselves" in capsys.readouterr().err
