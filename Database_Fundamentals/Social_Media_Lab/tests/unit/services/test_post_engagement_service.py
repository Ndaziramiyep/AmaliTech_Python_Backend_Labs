"""Unit tests for PostEngagementService."""

from __future__ import annotations

from datetime import datetime

import pytest

from social_platform.models.entities import Post
from social_platform.models.exceptions import PostNotFoundError
from social_platform.services.post_engagement_service import PostEngagementService
from tests.unit.services._fakes import FakeActivityLogRepository, FakePostRepository


def test_like_post_rejects_a_nonexistent_post(
    fake_post_repository: FakePostRepository,
    fake_activity_log_repository: FakeActivityLogRepository,
) -> None:
    """Liking a post that does not exist raises PostNotFoundError, not a silent no-op."""
    service = PostEngagementService(fake_post_repository, fake_activity_log_repository)

    with pytest.raises(PostNotFoundError):
        service.like_post(1, 999)
    assert fake_activity_log_repository.recorded_events == []


def test_like_post_records_a_post_liked_activity_event(
    fake_post_repository: FakePostRepository,
    fake_activity_log_repository: FakeActivityLogRepository,
) -> None:
    """Liking an existing post records exactly one post_liked activity event."""
    fake_post_repository.posts_by_id[10] = Post(10, 2, "hello", {}, datetime.now())
    service = PostEngagementService(fake_post_repository, fake_activity_log_repository)

    service.like_post(1, 10)

    assert len(fake_activity_log_repository.recorded_events) == 1
    assert fake_activity_log_repository.recorded_events[0].target_post_id == 10
