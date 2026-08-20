"""The post use cases: create, update, and delete."""

from __future__ import annotations

import logging
from datetime import UTC, datetime

from social_platform.common.exceptions import OwnershipError, PostNotFoundError
from social_platform.features.activity_log.model import ActivityEvent, ActivityEventType
from social_platform.features.activity_log.repository import ActivityLogRepository
from social_platform.features.posts.model import Post, PostMetadata
from social_platform.features.posts.repository import PostRepository
from social_platform.features.tags.repository import TagRepository

_logger = logging.getLogger(__name__)


class PostService:
    """Orchestrates creating, updating, and deleting posts, plus their activity events."""

    def __init__(
        self,
        post_repository: PostRepository,
        tag_repository: TagRepository,
        activity_log_repository: ActivityLogRepository,
    ) -> None:
        self._post_repository = post_repository
        self._tag_repository = tag_repository
        self._activity_log_repository = activity_log_repository

    def create_post(
        self,
        author_user_id: int,
        content: str,
        tags: list[str] | None = None,
        location: str | None = None,
    ) -> Post:
        """Create a post; `location` is stored as JSONB metadata, `tags` as real rows."""
        metadata: PostMetadata = {}
        if location:
            metadata["location"] = location

        post = self._post_repository.create_post(author_user_id, content, metadata)
        if tags:
            self._tag_repository.attach_tags(post.post_id, tags)
        self._log_event(ActivityEventType.POST_CREATED, author_user_id, post.post_id)
        return post

    def update_post(
        self,
        post_id: int,
        requesting_user_id: int,
        content: str,
        location: str | None = None,
    ) -> Post:
        """Update a post's content/location; only its author may update it."""
        self._require_ownership(post_id, requesting_user_id)

        metadata: PostMetadata = {}
        if location:
            metadata["location"] = location
        post = self._post_repository.update_post(post_id, requesting_user_id, content, metadata)
        self._log_event(ActivityEventType.POST_UPDATED, requesting_user_id, post_id)
        return post

    def delete_post(self, post_id: int, requesting_user_id: int) -> None:
        """Delete a post; only its author may delete it."""
        self._require_ownership(post_id, requesting_user_id)

        self._post_repository.delete_post(post_id, requesting_user_id)
        self._log_event(ActivityEventType.POST_DELETED, requesting_user_id, post_id)

    def get_posts_by_author(self, author_user_id: int, result_limit: int = 20) -> list[Post]:
        """Return an author's own posts, newest first."""
        return self._post_repository.find_posts_by_author(author_user_id, result_limit)

    def get_post(self, post_id: int) -> Post | None:
        """Return a post by id, or None if no such post exists."""
        return self._post_repository.find_post_by_id(post_id)

    def _require_ownership(self, post_id: int, requesting_user_id: int) -> None:
        post = self._post_repository.find_post_by_id(post_id)
        if post is None:
            raise PostNotFoundError(f"No post with id {post_id!r} exists.")
        if post.author_user_id != requesting_user_id:
            raise OwnershipError(f"User {requesting_user_id!r} does not own post {post_id!r}.")

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
