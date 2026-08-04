"""Factory for constructing a Redis client from application settings."""

from __future__ import annotations

import redis

from social_platform.config.application_settings import RedisSettings


def create_redis_client(settings: RedisSettings) -> redis.Redis:
    """Build a Redis client connected to the configured host, port, and database index."""
    return redis.Redis(
        host=settings.host,
        port=settings.port,
        db=settings.database_index,
        decode_responses=True,
    )
