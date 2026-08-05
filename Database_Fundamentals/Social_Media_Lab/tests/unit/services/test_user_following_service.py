"""Unit tests for UserFollowingService: the transactional follow/unfollow use case."""

from __future__ import annotations

import pytest

from social_platform.models.exceptions import InvalidFollowOperationError
from social_platform.models.results import FollowResult, UnfollowResult
from social_platform.services.user_following_service import UserFollowingService
from tests.unit.services._fakes import FakeActivityLogRepository, FakeFollowerRepository


def test_follow_user_rejects_following_oneself(
    fake_follower_repository: FakeFollowerRepository,
    fake_activity_log_repository: FakeActivityLogRepository,
) -> None:
    """A self-follow attempt is rejected before touching the repository."""
    service = UserFollowingService(fake_follower_repository, fake_activity_log_repository)

    with pytest.raises(InvalidFollowOperationError):
        service.follow_user(1, 1)
    assert fake_follower_repository.create_calls == []


def test_follow_user_logs_an_activity_event_only_when_newly_created(
    fake_follower_repository: FakeFollowerRepository,
    fake_activity_log_repository: FakeActivityLogRepository,
) -> None:
    """A fresh follow logs a user_followed activity event."""
    fake_follower_repository.follow_result_to_return = FollowResult.CREATED
    service = UserFollowingService(fake_follower_repository, fake_activity_log_repository)

    result = service.follow_user(1, 2)

    assert result is FollowResult.CREATED
    assert len(fake_activity_log_repository.recorded_events) == 1
    assert fake_activity_log_repository.recorded_events[0].actor_user_id == 1


def test_follow_user_does_not_log_an_activity_event_when_already_following(
    fake_follower_repository: FakeFollowerRepository,
    fake_activity_log_repository: FakeActivityLogRepository,
) -> None:
    """Re-following an already-followed user is idempotent and generates no new log entry."""
    fake_follower_repository.follow_result_to_return = FollowResult.ALREADY_EXISTS
    service = UserFollowingService(fake_follower_repository, fake_activity_log_repository)

    result = service.follow_user(1, 2)

    assert result is FollowResult.ALREADY_EXISTS
    assert fake_activity_log_repository.recorded_events == []


def test_follow_user_succeeds_even_when_activity_logging_fails(
    fake_follower_repository: FakeFollowerRepository,
) -> None:
    """A Mongo logging failure never undoes or fails an already-committed follow."""
    failing_activity_log_repository = FakeActivityLogRepository(
        raise_on_record=RuntimeError("boom")
    )
    fake_follower_repository.follow_result_to_return = FollowResult.CREATED
    service = UserFollowingService(fake_follower_repository, failing_activity_log_repository)

    result = service.follow_user(1, 2)

    assert result is FollowResult.CREATED


def test_unfollow_user_rejects_unfollowing_oneself(
    fake_follower_repository: FakeFollowerRepository,
    fake_activity_log_repository: FakeActivityLogRepository,
) -> None:
    """A self-unfollow attempt is rejected before touching the repository."""
    service = UserFollowingService(fake_follower_repository, fake_activity_log_repository)

    with pytest.raises(InvalidFollowOperationError):
        service.unfollow_user(1, 1)


def test_unfollow_user_reports_did_not_exist_without_logging_an_event(
    fake_follower_repository: FakeFollowerRepository,
    fake_activity_log_repository: FakeActivityLogRepository,
) -> None:
    """Unfollowing a user not followed is idempotent and generates no log entry."""
    fake_follower_repository.unfollow_result_to_return = UnfollowResult.DID_NOT_EXIST
    service = UserFollowingService(fake_follower_repository, fake_activity_log_repository)

    result = service.unfollow_user(1, 2)

    assert result is UnfollowResult.DID_NOT_EXIST
    assert fake_activity_log_repository.recorded_events == []
