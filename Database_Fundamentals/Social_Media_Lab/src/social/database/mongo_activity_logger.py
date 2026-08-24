"""Mongo-backed ActivityLogger that writes after the owning Postgres transaction commits, making it best-effort observability rather than part of the ACID boundary."""
from datetime import datetime, timezone
from typing import Any, Mapping

from pymongo import MongoClient


class MongoActivityLogger:
    """Implements the ActivityLogger protocol by writing records to a MongoDB collection."""

    def __init__(self, uri: str, db_name: str) -> None:
        """Connect to MongoDB and select the activity_log collection in the given database."""
        self._collection = MongoClient(uri)[db_name]["activity_log"]

    def log(self, activity_type: str, payload: Mapping[str, Any]) -> None:
        """Insert an activity record with its type and current UTC timestamp into the collection."""
        self._collection.insert_one(
            {
                "activity_type": activity_type,
                "logged_at": datetime.now(timezone.utc),
                **payload,
            }
        )
