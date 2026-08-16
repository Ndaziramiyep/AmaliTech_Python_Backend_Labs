"""Factory for constructing a MongoDB database handle from application settings."""

from __future__ import annotations

from typing import Any

from pymongo import MongoClient
from pymongo.database import Database

from social_platform.common.settings import MongoSettings


def create_mongo_database(settings: MongoSettings) -> Database[dict[str, Any]]:
    """Build a MongoDB database handle for the configured connection URI and database name."""
    client: MongoClient[dict[str, Any]] = MongoClient(settings.connection_uri)
    return client[settings.database_name]
