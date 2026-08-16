"""The post-creation use case."""

from __future__ import annotations

import logging
from datetime import UTC, datetime

from social_platform.features.activity_log.model import ActivityEvent, ActivityEventType
from social_platform.features.activity_log.repository import ActivityLogRepository
from social_platform.features.posts.model import Post, PostMetadata
from social_platform.features.posts.repository import PostRepository

_logger = logging.getLogger(__name__)


class PostService:
    """Orchestrates creating a post and best-effort logging the resulting activity event."""

    def __init__(
        self, post_repository: PostRepository, activity_log_repository: ActivityLogRepository
    ) -> None:
        self._post_repository = post_repository
        self._activity_log_repository = activity_log_repository

    def create_post(
        self,
        author_user_id: int,
        content: str,
        tags: list[str] | None = None,
        location: str | None = None,
    ) -> Post:
        """Create a post, storing any tags/location as JSONB metadata."""
        metadata: PostMetadata = {}
        if tags:
            metadata["tags"] = tags
        if location:
            metadata["location"] = location

        post = self._post_repository.create_post(author_user_id, content, metadata)
        try:
            self._activity_log_repository.record_activity_event(
                ActivityEvent(
                    event_type=ActivityEventType.POST_CREATED,
                    actor_user_id=author_user_id,
                    occurred_at=datetime.now(UTC),
                    target_post_id=post.post_id,
                )
            )
        except Exception:
            _logger.exception(
                "Failed to record post_created activity event for post %s.", post.post_id
            )
        return post
