"""Domain entities shared across repositories, services, and the CLI layer."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Any, TypedDict


class PostMetadata(TypedDict, total=False):
    """Free-form JSONB payload stored alongside a post: tags and location."""

    tags: list[str]
    location: str


@dataclass(frozen=True, slots=True)
class User:
    """A registered platform user (never carries a password hash)."""

    user_id: int
    username: str
    email: str
    display_name: str
    created_at: datetime


@dataclass(frozen=True, slots=True)
class Post:
    """A single post authored by a user."""

    post_id: int
    author_user_id: int
    content: str
    metadata: PostMetadata
    created_at: datetime


@dataclass(frozen=True, slots=True)
class Comment:
    """A comment left by a user on a post."""

    comment_id: int
    post_id: int
    commenter_user_id: int
    content: str
    created_at: datetime


@dataclass(frozen=True, slots=True)
class FollowRelationship:
    """A directed follow edge: ``follower_user_id`` follows ``followee_user_id``."""

    follower_user_id: int
    followee_user_id: int
    created_at: datetime


@dataclass(frozen=True, slots=True)
class FeedPostEntry:
    """One page row of a user's timeline feed, including the author's username."""

    post_id: int
    author_user_id: int
    author_username: str
    content: str
    metadata: PostMetadata
    created_at: datetime


@dataclass(frozen=True, slots=True)
class TrendingPostEntry:
    """One ranked row of the trending-posts query, including its comment count."""

    post_id: int
    author_user_id: int
    content: str
    metadata: PostMetadata
    created_at: datetime
    comment_count: int


class ActivityEventType(StrEnum):
    """The kinds of activity events recorded in the MongoDB activity log."""

    USER_FOLLOWED = "user_followed"
    USER_UNFOLLOWED = "user_unfollowed"
    POST_CREATED = "post_created"
    COMMENT_CREATED = "comment_created"
    POST_LIKED = "post_liked"


@dataclass(frozen=True, slots=True)
class ActivityEvent:
    """A single activity log entry destined for MongoDB."""

    event_type: ActivityEventType
    actor_user_id: int
    occurred_at: datetime
    target_user_id: int | None = None
    target_post_id: int | None = None
    details: dict[str, Any] | None = None
