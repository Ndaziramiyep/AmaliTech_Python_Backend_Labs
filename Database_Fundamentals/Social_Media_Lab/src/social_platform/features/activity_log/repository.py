"""Activity log persistence: the `ActivityLogRepository` contract and its MongoDB implementation."""

from __future__ import annotations

from typing import Any, Protocol

from pymongo.database import Database

from social_platform.features.activity_log.model import ActivityEvent

_ACTIVITY_LOG_COLLECTION_NAME = "activity_logs"


class ActivityLogRepository(Protocol):
    """Persistence contract for the activity log. Services depend on this, not on Mongo."""

    def record_activity_event(self, event: ActivityEvent) -> None:
        """Append an activity event to the activity log."""


class MongoActivityLogRepository:
    """Implements `ActivityLogRepository` against a MongoDB database handle."""

    def __init__(self, mongo_database: Database[dict[str, Any]]) -> None:
        self._activity_log_collection = mongo_database[_ACTIVITY_LOG_COLLECTION_NAME]

    def record_activity_event(self, event: ActivityEvent) -> None:
        """Insert one activity event document into the activity log collection."""
        self._activity_log_collection.insert_one(
            {
                "event_type": event.event_type.value,
                "actor_user_id": event.actor_user_id,
                "target_user_id": event.target_user_id,
                "target_post_id": event.target_post_id,
                "occurred_at": event.occurred_at,
                "details": event.details or {},
            }
        )
