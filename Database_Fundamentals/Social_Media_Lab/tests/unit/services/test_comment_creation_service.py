"""Unit tests for CommentService.create_comment and get_comment_thread."""

from __future__ import annotations

import pytest

from social_platform.common.exceptions import CommentNotFoundError, InvalidCommentOperationError
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


def test_create_comment_as_a_reply_links_it_to_its_parent(
    fake_comment_repository: FakeCommentRepository,
    fake_activity_log_repository: FakeActivityLogRepository,
) -> None:
    """A reply's parent_comment_id is set when it belongs to the same post."""
    service = CommentService(fake_comment_repository, fake_activity_log_repository)
    top_level = service.create_comment(10, 1, "nice post")

    reply = service.create_comment(10, 2, "thanks!", top_level.comment_id)

    assert reply.parent_comment_id == top_level.comment_id


def test_create_comment_rejects_a_reply_to_a_nonexistent_parent(
    fake_comment_repository: FakeCommentRepository,
    fake_activity_log_repository: FakeActivityLogRepository,
) -> None:
    """Replying to a comment id that doesn't exist is a clean not-found error."""
    service = CommentService(fake_comment_repository, fake_activity_log_repository)

    with pytest.raises(CommentNotFoundError):
        service.create_comment(10, 1, "thanks!", 999)


def test_create_comment_rejects_a_reply_to_a_comment_on_a_different_post(
    fake_comment_repository: FakeCommentRepository,
    fake_activity_log_repository: FakeActivityLogRepository,
) -> None:
    """A reply's parent must belong to the same post it's replying within."""
    service = CommentService(fake_comment_repository, fake_activity_log_repository)
    other_posts_comment = service.create_comment(20, 1, "on a different post")

    with pytest.raises(InvalidCommentOperationError):
        service.create_comment(10, 2, "thanks!", other_posts_comment.comment_id)


def test_get_comment_thread_returns_comments_depth_first(
    fake_comment_repository: FakeCommentRepository,
    fake_activity_log_repository: FakeActivityLogRepository,
) -> None:
    """A top-level comment and its reply come back in depth-first thread order."""
    service = CommentService(fake_comment_repository, fake_activity_log_repository)
    top_level = service.create_comment(10, 1, "nice post")
    service.create_comment(10, 2, "thanks!", top_level.comment_id)

    thread = service.get_comment_thread(10)

    assert [entry.depth for entry in thread] == [0, 1]
