"""MongoDB-backed persistence for the activity log (likes, follows, and similar events)."""

from __future__ import annotations

from typing import Any

from pymongo.database import Database

from social_platform.models.entities import ActivityEvent
from social_platform.repositories.interfaces import ActivityLogRepositoryInterface

_ACTIVITY_LOG_COLLECTION_NAME = "activity_logs"


class MongoActivityLogRepository(ActivityLogRepositoryInterface):
    """Implements `ActivityLogRepositoryInterface` against a MongoDB database handle."""

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
