"""Unit tests for CommentService.delete_comment."""

from __future__ import annotations

import pytest

from social_platform.common.exceptions import CommentNotFoundError, OwnershipError
from social_platform.features.comments.service import CommentService
from tests.unit.services._fakes import FakeActivityLogRepository, FakeCommentRepository


def test_delete_comment_rejects_a_non_owner(
    fake_comment_repository: FakeCommentRepository,
    fake_activity_log_repository: FakeActivityLogRepository,
) -> None:
    """Deleting someone else's comment raises OwnershipError, and the comment survives."""
    comment = fake_comment_repository.create_comment(10, 1, "nice post")
    service = CommentService(fake_comment_repository, fake_activity_log_repository)

    with pytest.raises(OwnershipError):
        service.delete_comment(comment.comment_id, 999)
    assert fake_comment_repository.find_comment_by_id(comment.comment_id) is not None


def test_delete_comment_rejects_a_nonexistent_comment(
    fake_comment_repository: FakeCommentRepository,
    fake_activity_log_repository: FakeActivityLogRepository,
) -> None:
    """Deleting a comment that doesn't exist raises CommentNotFoundError."""
    service = CommentService(fake_comment_repository, fake_activity_log_repository)

    with pytest.raises(CommentNotFoundError):
        service.delete_comment(999, 1)


def test_delete_comment_by_the_owner_removes_it(
    fake_comment_repository: FakeCommentRepository,
    fake_activity_log_repository: FakeActivityLogRepository,
) -> None:
    """The commenter can delete their own comment."""
    comment = fake_comment_repository.create_comment(10, 1, "nice post")
    service = CommentService(fake_comment_repository, fake_activity_log_repository)

    service.delete_comment(comment.comment_id, 1)

    assert fake_comment_repository.find_comment_by_id(comment.comment_id) is None


def test_delete_comment_logs_a_comment_deleted_activity_event(
    fake_comment_repository: FakeCommentRepository,
    fake_activity_log_repository: FakeActivityLogRepository,
) -> None:
    """Deleting a comment logs exactly one comment_deleted activity event."""
    comment = fake_comment_repository.create_comment(10, 1, "nice post")
    service = CommentService(fake_comment_repository, fake_activity_log_repository)

    service.delete_comment(comment.comment_id, 1)

    assert len(fake_activity_log_repository.recorded_events) == 1
    assert fake_activity_log_repository.recorded_events[0].target_post_id == 10
