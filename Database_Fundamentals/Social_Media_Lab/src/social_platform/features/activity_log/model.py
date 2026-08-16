"""The activity event recorded in the MongoDB activity log."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Any


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
