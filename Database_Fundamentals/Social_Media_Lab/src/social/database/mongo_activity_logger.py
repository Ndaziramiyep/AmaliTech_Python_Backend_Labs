"""Mongo-backed implementation of the ActivityLogger protocol.

Writes happen after the owning Postgres transaction has committed (see the
service docstrings), so a failure here never rolls back the write it's
logging - it's best-effort observability, not part of the ACID boundary.
"""
from datetime import datetime, timezone
from typing import Any, Mapping

from pymongo import MongoClient


class MongoActivityLogger:
    def __init__(self, uri: str, db_name: str) -> None:
        self._collection = MongoClient(uri)[db_name]["activity_log"]

    def log(self, activity_type: str, payload: Mapping[str, Any]) -> None:
        self._collection.insert_one(
            {
                "activity_type": activity_type,
                "logged_at": datetime.now(timezone.utc),
                **payload,
            }
        )
