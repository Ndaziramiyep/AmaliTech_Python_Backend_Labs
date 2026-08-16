"""Unit tests for CommentService.create_comment."""

from __future__ import annotations

from social_platform.features.comments.service import CommentService
from tests.unit.services._fakes import FakeActivityLogRepository, FakeCommentRepository


def test_create_comment_logs_a_comment_created_activity_event(
    fake_comment_repository: FakeCommentRepository,
    fake_activity_log_repository: FakeActivityLogRepository,
) -> None:
    """Creating a comment logs exactly one comment_created activity event."""
    service = CommentService(fake_comment_repository, fake_activity_log_repository)

    comment = service.create_comment(10, 1, "nice post")

    assert comment.content == "nice post"
    assert len(fake_activity_log_repository.recorded_events) == 1
    assert fake_activity_log_repository.recorded_events[0].target_post_id == 10


def test_create_comment_succeeds_even_when_activity_logging_fails(
    fake_comment_repository: FakeCommentRepository,
) -> None:
    """A Mongo logging failure never undoes or fails an already-committed comment."""
    failing_activity_log_repository = FakeActivityLogRepository(
        raise_on_record=RuntimeError("boom")
    )
    service = CommentService(fake_comment_repository, failing_activity_log_repository)

    comment = service.create_comment(10, 1, "nice post")

    assert comment.post_id == 10
