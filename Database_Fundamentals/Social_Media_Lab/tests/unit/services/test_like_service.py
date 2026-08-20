"""Unit tests for LikeService.like_post and unlike_post."""

from __future__ import annotations

from datetime import datetime

import pytest

from social_platform.common.exceptions import PostNotFoundError
from social_platform.features.likes.model import LikeResult, UnlikeResult
from social_platform.features.likes.service import LikeService
from social_platform.features.posts.model import Post
from tests.unit.services._fakes import (
    FakeActivityLogRepository,
    FakeLikeRepository,
    FakePostRepository,
)


def test_like_post_rejects_a_nonexistent_post(
    fake_post_repository: FakePostRepository,
    fake_like_repository: FakeLikeRepository,
    fake_activity_log_repository: FakeActivityLogRepository,
) -> None:
    """Liking a post that does not exist raises PostNotFoundError, not a silent no-op."""
    service = LikeService(fake_post_repository, fake_like_repository, fake_activity_log_repository)

    with pytest.raises(PostNotFoundError):
        service.like_post(1, 999)
    assert fake_like_repository.create_calls == []
    assert fake_activity_log_repository.recorded_events == []


def test_like_post_records_a_post_liked_activity_event_when_newly_created(
    fake_post_repository: FakePostRepository,
    fake_like_repository: FakeLikeRepository,
    fake_activity_log_repository: FakeActivityLogRepository,
) -> None:
    """Liking an existing post for the first time records one post_liked activity event."""
    fake_post_repository.posts_by_id[10] = Post(10, 2, "hello", {}, datetime.now())
    fake_like_repository.like_result_to_return = LikeResult.CREATED
    service = LikeService(fake_post_repository, fake_like_repository, fake_activity_log_repository)

    result = service.like_post(1, 10)

    assert result is LikeResult.CREATED
    assert len(fake_activity_log_repository.recorded_events) == 1
    assert fake_activity_log_repository.recorded_events[0].target_post_id == 10


def test_like_post_does_not_log_an_activity_event_when_already_liked(
    fake_post_repository: FakePostRepository,
    fake_like_repository: FakeLikeRepository,
    fake_activity_log_repository: FakeActivityLogRepository,
) -> None:
    """Liking a post a second time is idempotent and generates no new log entry."""
    fake_post_repository.posts_by_id[10] = Post(10, 2, "hello", {}, datetime.now())
    fake_like_repository.like_result_to_return = LikeResult.ALREADY_EXISTS
    service = LikeService(fake_post_repository, fake_like_repository, fake_activity_log_repository)

    result = service.like_post(1, 10)

    assert result is LikeResult.ALREADY_EXISTS
    assert fake_activity_log_repository.recorded_events == []


def test_like_post_succeeds_even_when_activity_logging_fails(
    fake_post_repository: FakePostRepository, fake_like_repository: FakeLikeRepository
) -> None:
    """A Mongo logging failure never undoes or fails an already-committed like."""
    fake_post_repository.posts_by_id[10] = Post(10, 2, "hello", {}, datetime.now())
    fake_like_repository.like_result_to_return = LikeResult.CREATED
    failing_activity_log_repository = FakeActivityLogRepository(
        raise_on_record=RuntimeError("boom")
    )
    service = LikeService(
        fake_post_repository, fake_like_repository, failing_activity_log_repository
    )

    result = service.like_post(1, 10)

    assert result is LikeResult.CREATED


def test_unlike_post_records_a_post_unliked_activity_event_when_removed(
    fake_post_repository: FakePostRepository,
    fake_like_repository: FakeLikeRepository,
    fake_activity_log_repository: FakeActivityLogRepository,
) -> None:
    """Removing an actual like records one post_unliked activity event."""
    fake_like_repository.unlike_result_to_return = UnlikeResult.REMOVED
    service = LikeService(fake_post_repository, fake_like_repository, fake_activity_log_repository)

    result = service.unlike_post(1, 10)

    assert result is UnlikeResult.REMOVED
    assert fake_like_repository.delete_calls == [(10, 1)]
    assert len(fake_activity_log_repository.recorded_events) == 1
    assert fake_activity_log_repository.recorded_events[0].target_post_id == 10


def test_unlike_post_does_not_log_an_event_when_it_was_not_liked(
    fake_post_repository: FakePostRepository,
    fake_like_repository: FakeLikeRepository,
    fake_activity_log_repository: FakeActivityLogRepository,
) -> None:
    """Unliking a post you never liked is idempotent and generates no log entry."""
    fake_like_repository.unlike_result_to_return = UnlikeResult.DID_NOT_EXIST
    service = LikeService(fake_post_repository, fake_like_repository, fake_activity_log_repository)

    result = service.unlike_post(1, 10)

    assert result is UnlikeResult.DID_NOT_EXIST
    assert fake_activity_log_repository.recorded_events == []


def test_has_liked_passes_through_to_the_repository(
    fake_post_repository: FakePostRepository,
    fake_like_repository: FakeLikeRepository,
    fake_activity_log_repository: FakeActivityLogRepository,
) -> None:
    """has_liked reflects whatever the repository reports."""
    fake_like_repository.has_liked_to_return = True
    service = LikeService(fake_post_repository, fake_like_repository, fake_activity_log_repository)

    assert service.has_liked(1, 10) is True
