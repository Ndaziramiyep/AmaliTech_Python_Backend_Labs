"""Fixtures for integration tests: real PostgreSQL, Redis, and MongoDB via docker-compose.

Each repository call commits its own short transaction (correct for a connection-pooled
service used by many independent CLI invocations), so per-test isolation here is achieved
by truncating the relevant tables/collections before each test rather than by rolling back
one enclosing transaction.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

import pytest
import redis
from pymongo.database import Database

from social_platform.config.application_settings import ApplicationSettings
from social_platform.database.mongo_connection_factory import create_mongo_database
from social_platform.database.postgres_connection_pool import PostgresConnectionPool
from social_platform.database.redis_connection_factory import create_redis_client
from social_platform.models.entities import User
from social_platform.repositories.postgres_user_repository import PostgresUserRepository

_settings = ApplicationSettings.from_environment()


@pytest.fixture
def connection_pool() -> Iterator[PostgresConnectionPool]:
    """A real PostgresConnectionPool, with all four tables truncated before each test."""
    pool = PostgresConnectionPool(_settings.postgres)
    with pool.cursor() as cursor:
        cursor.execute("TRUNCATE followers, comments, posts, users RESTART IDENTITY CASCADE")
    yield pool
    pool.close_all_connections()


@pytest.fixture
def redis_client() -> redis.Redis:
    """A real Redis client, flushed before each test."""
    client = create_redis_client(_settings.redis)
    client.flushdb()
    return client


@pytest.fixture
def mongo_database() -> Database[dict[str, Any]]:
    """A real MongoDB database handle, with the activity log collection cleared."""
    database = create_mongo_database(_settings.mongo)
    database["activity_logs"].delete_many({})
    return database


@pytest.fixture
def existing_users(connection_pool: PostgresConnectionPool) -> tuple[User, User]:
    """Two real user rows to exercise follow/unfollow/post/comment operations against."""
    user_repository = PostgresUserRepository(connection_pool)
    first_user = user_repository.create_user("ada", "ada@example.com", "hash", "Ada Lovelace")
    second_user = user_repository.create_user("grace", "grace@example.com", "hash", "Grace Hopper")
    return first_user, second_user
