"""Unit tests for MongoActivityLogRepository, backed by an in-memory mongomock database."""

from __future__ import annotations

from datetime import datetime
from typing import Any

import mongomock
from pymongo.database import Database

from social_platform.models.entities import ActivityEvent, ActivityEventType
from social_platform.repositories.mongo_activity_log_repository import (
    MongoActivityLogRepository,
)


def test_record_activity_event_inserts_one_document_with_every_field(
    sample_created_at: datetime,
) -> None:
    """Recording an event inserts exactly one document with every field."""
    mongo_database: Database[dict[str, Any]] = mongomock.MongoClient()["social_platform"]
    repository = MongoActivityLogRepository(mongo_database)

    repository.record_activity_event(
        ActivityEvent(
            event_type=ActivityEventType.USER_FOLLOWED,
            actor_user_id=1,
            occurred_at=sample_created_at,
            target_user_id=2,
        )
    )

    documents = list(mongo_database["activity_logs"].find())
    assert len(documents) == 1
    assert documents[0]["event_type"] == "user_followed"
    assert documents[0]["actor_user_id"] == 1
    assert documents[0]["target_user_id"] == 2
    assert documents[0]["target_post_id"] is None
