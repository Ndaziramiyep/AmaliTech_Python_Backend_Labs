"""The post-engagement use case: liking a post."""

from __future__ import annotations

from datetime import UTC, datetime

from social_platform.models.entities import ActivityEvent, ActivityEventType
from social_platform.models.exceptions import PostNotFoundError
from social_platform.repositories.interfaces import (
    ActivityLogRepositoryInterface,
    PostRepositoryInterface,
)


class PostEngagementService:
    """Orchestrates lightweight engagement actions that live only in the activity log."""

    def __init__(
        self,
        post_repository: PostRepositoryInterface,
        activity_log_repository: ActivityLogRepositoryInterface,
    ) -> None:
        self._post_repository = post_repository
        self._activity_log_repository = activity_log_repository

    def like_post(self, actor_user_id: int, post_id: int) -> None:
        """Record a like against an existing post. Likes live only in the Mongo activity log."""
        if self._post_repository.find_post_by_id(post_id) is None:
            raise PostNotFoundError(f"No post with id {post_id!r} exists.")

        self._activity_log_repository.record_activity_event(
            ActivityEvent(
                event_type=ActivityEventType.POST_LIKED,
                actor_user_id=actor_user_id,
                occurred_at=datetime.now(UTC),
                target_post_id=post_id,
            )
        )
