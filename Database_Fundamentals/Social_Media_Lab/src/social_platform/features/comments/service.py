"""The comment use cases: create (optionally as a reply), delete, and read a thread."""

from __future__ import annotations

import logging
from datetime import UTC, datetime

from social_platform.common.exceptions import (
    CommentNotFoundError,
    InvalidCommentOperationError,
    OwnershipError,
)
from social_platform.features.activity_log.model import ActivityEvent, ActivityEventType
from social_platform.features.activity_log.repository import ActivityLogRepository
from social_platform.features.comments.model import Comment, CommentThreadEntry
from social_platform.features.comments.repository import CommentRepository

_logger = logging.getLogger(__name__)


class CommentService:
    """Orchestrates creating, deleting, and reading comments, plus their activity events."""

    def __init__(
        self,
        comment_repository: CommentRepository,
        activity_log_repository: ActivityLogRepository,
    ) -> None:
        self._comment_repository = comment_repository
        self._activity_log_repository = activity_log_repository

    def create_comment(
        self,
        post_id: int,
        commenter_user_id: int,
        content: str,
        parent_comment_id: int | None = None,
    ) -> Comment:
        """Create a comment on a post, or a reply to another comment on that same post."""
        if parent_comment_id is not None:
            parent_comment = self._comment_repository.find_comment_by_id(parent_comment_id)
            if parent_comment is None:
                raise CommentNotFoundError(f"No comment with id {parent_comment_id!r} exists.")
            if parent_comment.post_id != post_id:
                raise InvalidCommentOperationError(
                    f"Comment {parent_comment_id!r} does not belong to post {post_id!r}."
                )

        comment = self._comment_repository.create_comment(
            post_id, commenter_user_id, content, parent_comment_id
        )
        self._log_event(ActivityEventType.COMMENT_CREATED, commenter_user_id, post_id)
        return comment

    def get_comment_thread(self, post_id: int) -> list[CommentThreadEntry]:
        """Return every comment on a post, depth-first: each reply follows its parent."""
        return self._comment_repository.find_comment_thread_for_post(post_id)

    def delete_comment(self, comment_id: int, requesting_user_id: int) -> None:
        """Delete a comment; only the user who wrote it may delete it."""
        comment = self._comment_repository.find_comment_by_id(comment_id)
        if comment is None:
            raise CommentNotFoundError(f"No comment with id {comment_id!r} exists.")
        if comment.commenter_user_id != requesting_user_id:
            raise OwnershipError(
                f"User {requesting_user_id!r} does not own comment {comment_id!r}."
            )

        self._comment_repository.delete_comment(comment_id, requesting_user_id)
        self._log_event(ActivityEventType.COMMENT_DELETED, requesting_user_id, comment.post_id)

    def _log_event(
        self, event_type: ActivityEventType, actor_user_id: int, target_post_id: int
    ) -> None:
        try:
            self._activity_log_repository.record_activity_event(
                ActivityEvent(
                    event_type=event_type,
                    actor_user_id=actor_user_id,
                    occurred_at=datetime.now(UTC),
                    target_post_id=target_post_id,
                )
            )
        except Exception:
            _logger.exception(
                "Failed to record %s activity event for post %s.", event_type.value, target_post_id
            )
