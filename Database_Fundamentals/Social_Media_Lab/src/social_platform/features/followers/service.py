"""The transactional follow/unfollow use case."""

from __future__ import annotations

import logging
from datetime import UTC, datetime

from social_platform.common.exceptions import InvalidFollowOperationError
from social_platform.features.activity_log.model import ActivityEvent, ActivityEventType
from social_platform.features.activity_log.repository import ActivityLogRepository
from social_platform.features.followers.model import FollowResult, UnfollowResult
from social_platform.features.followers.repository import FollowerRepository

_logger = logging.getLogger(__name__)


class FollowService:
    """Orchestrates following and unfollowing users.

    The PostgreSQL follow/unfollow edge (see `PostgresFollowerRepository`) is the
    transactional source of truth. The MongoDB activity-log write below happens only
    after that transaction commits and is best-effort: a logging failure is caught and
    reported, never allowed to undo or fail the already-committed follow/unfollow.
    Cross-store two-phase commit is intentionally out of scope for this lab.
    """

    def __init__(
        self,
        follower_repository: FollowerRepository,
        activity_log_repository: ActivityLogRepository,
    ) -> None:
        self._follower_repository = follower_repository
        self._activity_log_repository = activity_log_repository

    def follow_user(self, follower_user_id: int, followee_user_id: int) -> FollowResult:
        """Create a follow edge; re-following the same user is idempotent, not an error."""
        if follower_user_id == followee_user_id:
            raise InvalidFollowOperationError("A user cannot follow themselves.")

        result = self._follower_repository.create_follow_relationship(
            follower_user_id, followee_user_id
        )
        if result is FollowResult.CREATED:
            self._log_activity_event(
                ActivityEventType.USER_FOLLOWED, follower_user_id, followee_user_id
            )
        return result

    def unfollow_user(self, follower_user_id: int, followee_user_id: int) -> UnfollowResult:
        """Remove a follow edge; unfollowing a user not followed is idempotent, not an error."""
        if follower_user_id == followee_user_id:
            raise InvalidFollowOperationError("A user cannot unfollow themselves.")

        result = self._follower_repository.delete_follow_relationship(
            follower_user_id, followee_user_id
        )
        if result is UnfollowResult.REMOVED:
            self._log_activity_event(
                ActivityEventType.USER_UNFOLLOWED, follower_user_id, followee_user_id
            )
        return result

    def is_following(self, follower_user_id: int, followee_user_id: int) -> bool:
        """Return whether `follower_user_id` currently follows `followee_user_id`."""
        return self._follower_repository.is_following(follower_user_id, followee_user_id)

    def _log_activity_event(
        self, event_type: ActivityEventType, actor_user_id: int, target_user_id: int
    ) -> None:
        try:
            self._activity_log_repository.record_activity_event(
                ActivityEvent(
                    event_type=event_type,
                    actor_user_id=actor_user_id,
                    occurred_at=datetime.now(UTC),
                    target_user_id=target_user_id,
                )
            )
        except Exception:
            _logger.exception(
                "Failed to record %s activity event for actor %s targeting %s.",
                event_type.value,
                actor_user_id,
                target_user_id,
            )
