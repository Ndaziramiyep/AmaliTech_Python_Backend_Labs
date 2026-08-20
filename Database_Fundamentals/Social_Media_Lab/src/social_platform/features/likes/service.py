"""The like/unlike use cases.

Liking is a real relational fact now (see `sql/schema.sql`'s `likes` table), not just
an activity-log entry -- PostgreSQL is the source of truth for *whether* a post is
liked; MongoDB's activity log only records that the like/unlike *event* happened,
exactly like every other action in this app.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime

from social_platform.common.exceptions import PostNotFoundError
from social_platform.features.activity_log.model import ActivityEvent, ActivityEventType
from social_platform.features.activity_log.repository import ActivityLogRepository
from social_platform.features.likes.model import LikeResult, UnlikeResult
from social_platform.features.likes.repository import LikeRepository
from social_platform.features.posts.repository import PostRepository

_logger = logging.getLogger(__name__)


class LikeService:
    """Orchestrates liking/unliking a post, plus a best-effort activity event."""

    def __init__(
        self,
        post_repository: PostRepository,
        like_repository: LikeRepository,
        activity_log_repository: ActivityLogRepository,
    ) -> None:
        self._post_repository = post_repository
        self._like_repository = like_repository
        self._activity_log_repository = activity_log_repository

    def like_post(self, actor_user_id: int, post_id: int) -> LikeResult:
        """Like an existing post; liking the same post twice is idempotent, not an error."""
        if self._post_repository.find_post_by_id(post_id) is None:
            raise PostNotFoundError(f"No post with id {post_id!r} exists.")

        result = self._like_repository.create_like(post_id, actor_user_id)
        if result is LikeResult.CREATED:
            self._log_event(ActivityEventType.POST_LIKED, actor_user_id, post_id)
        return result

    def unlike_post(self, actor_user_id: int, post_id: int) -> UnlikeResult:
        """Remove a like; unliking a post not liked is idempotent, not an error."""
        result = self._like_repository.delete_like(post_id, actor_user_id)
        if result is UnlikeResult.REMOVED:
            self._log_event(ActivityEventType.POST_UNLIKED, actor_user_id, post_id)
        return result

    def has_liked(self, actor_user_id: int, post_id: int) -> bool:
        """Return whether `actor_user_id` currently has a like recorded on `post_id`."""
        return self._like_repository.has_user_liked(post_id, actor_user_id)

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
