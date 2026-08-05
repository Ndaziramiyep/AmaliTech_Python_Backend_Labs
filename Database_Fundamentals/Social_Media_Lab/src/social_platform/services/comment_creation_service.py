"""The comment-creation use case."""

from __future__ import annotations

import logging
from datetime import UTC, datetime

from social_platform.models.entities import ActivityEvent, ActivityEventType, Comment
from social_platform.repositories.interfaces import (
    ActivityLogRepositoryInterface,
    CommentRepositoryInterface,
)

_logger = logging.getLogger(__name__)


class CommentCreationService:
    """Orchestrates creating a comment and best-effort logging the resulting activity event."""

    def __init__(
        self,
        comment_repository: CommentRepositoryInterface,
        activity_log_repository: ActivityLogRepositoryInterface,
    ) -> None:
        self._comment_repository = comment_repository
        self._activity_log_repository = activity_log_repository

    def create_comment(self, post_id: int, commenter_user_id: int, content: str) -> Comment:
        """Create a comment on an existing post."""
        comment = self._comment_repository.create_comment(post_id, commenter_user_id, content)
        try:
            self._activity_log_repository.record_activity_event(
                ActivityEvent(
                    event_type=ActivityEventType.COMMENT_CREATED,
                    actor_user_id=commenter_user_id,
                    occurred_at=datetime.now(UTC),
                    target_post_id=post_id,
                )
            )
        except Exception:
            _logger.exception(
                "Failed to record comment_created activity event for post %s.", post_id
            )
        return comment
