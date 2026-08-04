"""Abstract repository interfaces. Services depend on these, never on concrete stores."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime

from social_platform.models.entities import (
    ActivityEvent,
    Comment,
    FeedPostEntry,
    Post,
    PostMetadata,
    TrendingPostEntry,
    User,
)
from social_platform.models.results import FollowResult, UnfollowResult


class UserRepositoryInterface(ABC):
    """Persistence contract for user accounts."""

    @abstractmethod
    def create_user(self, username: str, email: str, password_hash: str, display_name: str) -> User:
        """Persist a new user and return the created entity."""

    @abstractmethod
    def find_user_by_id(self, user_id: int) -> User | None:
        """Return the user with the given id, or None if no such user exists."""

    @abstractmethod
    def find_user_and_password_hash_by_username(self, username: str) -> tuple[User, str] | None:
        """Return the user and their password hash for a username, or None if no match."""


class PostRepositoryInterface(ABC):
    """Persistence contract for posts, the timeline feed query, and trending posts."""

    @abstractmethod
    def create_post(self, author_user_id: int, content: str, metadata: PostMetadata) -> Post:
        """Persist a new post and return the created entity."""

    @abstractmethod
    def find_post_by_id(self, post_id: int) -> Post | None:
        """Return the post with the given id, or None if no such post exists."""

    @abstractmethod
    def fetch_timeline_feed_page(
        self, follower_user_id: int, first_row: int, last_row: int
    ) -> list[FeedPostEntry]:
        """Return one paginated, chronologically ordered page of a user's timeline feed."""

    @abstractmethod
    def fetch_trending_posts(self, since: datetime, result_limit: int) -> list[TrendingPostEntry]:
        """Return posts created since `since`, ranked by their recent comment count."""


class CommentRepositoryInterface(ABC):
    """Persistence contract for comments."""

    @abstractmethod
    def create_comment(self, post_id: int, commenter_user_id: int, content: str) -> Comment:
        """Persist a new comment and return the created entity."""


class FollowerRepositoryInterface(ABC):
    """Persistence contract for the follower graph."""

    @abstractmethod
    def create_follow_relationship(
        self, follower_user_id: int, followee_user_id: int
    ) -> FollowResult:
        """Create a follow edge, or report that it already existed."""

    @abstractmethod
    def delete_follow_relationship(
        self, follower_user_id: int, followee_user_id: int
    ) -> UnfollowResult:
        """Remove a follow edge, or report that it did not exist."""


class TimelineCacheRepositoryInterface(ABC):
    """Cache contract for pre-rendered timeline feed pages."""

    @abstractmethod
    def get_cached_feed_page(
        self, follower_user_id: int, page_number: int
    ) -> list[FeedPostEntry] | None:
        """Return a cached feed page, or None on a cache miss."""

    @abstractmethod
    def set_cached_feed_page(
        self, follower_user_id: int, page_number: int, feed_page: list[FeedPostEntry]
    ) -> None:
        """Cache a feed page for the configured time-to-live."""


class ActivityLogRepositoryInterface(ABC):
    """Persistence contract for the activity log (likes, follows, and similar events)."""

    @abstractmethod
    def record_activity_event(self, event: ActivityEvent) -> None:
        """Append an activity event to the activity log."""
