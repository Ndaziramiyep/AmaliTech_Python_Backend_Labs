"""Environment-driven configuration for PostgreSQL, Redis, and MongoDB connections."""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True, slots=True)
class PostgresSettings:
    """Connection and pool-sizing settings for PostgreSQL."""

    host: str
    port: int
    database_name: str
    username: str
    password: str
    pool_min_size: int
    pool_max_size: int

    @classmethod
    def from_environment(cls) -> PostgresSettings:
        """Build settings from `POSTGRES_*` environment variables."""
        return cls(
            host=os.environ.get("POSTGRES_HOST", "localhost"),
            port=int(os.environ.get("POSTGRES_PORT", "5433")),
            database_name=os.environ.get("POSTGRES_DB", "social_platform"),
            username=os.environ.get("POSTGRES_USER", "social_platform"),
            password=os.environ.get("POSTGRES_PASSWORD", "social_platform"),
            pool_min_size=int(os.environ.get("POSTGRES_POOL_MIN_SIZE", "1")),
            pool_max_size=int(os.environ.get("POSTGRES_POOL_MAX_SIZE", "10")),
        )


@dataclass(frozen=True, slots=True)
class RedisSettings:
    """Connection settings and cache policy for the Redis timeline cache."""

    host: str
    port: int
    database_index: int
    timeline_cache_ttl_seconds: int

    @classmethod
    def from_environment(cls) -> RedisSettings:
        """Build settings from `REDIS_*` and `TIMELINE_CACHE_*` environment variables."""
        return cls(
            host=os.environ.get("REDIS_HOST", "localhost"),
            port=int(os.environ.get("REDIS_PORT", "6379")),
            database_index=int(os.environ.get("REDIS_DB", "0")),
            timeline_cache_ttl_seconds=int(os.environ.get("TIMELINE_CACHE_TTL_SECONDS", "60")),
        )


@dataclass(frozen=True, slots=True)
class MongoSettings:
    """Connection settings for the MongoDB activity log store."""

    connection_uri: str
    database_name: str

    @classmethod
    def from_environment(cls) -> MongoSettings:
        """Build settings from `MONGO_*` environment variables."""
        return cls(
            connection_uri=os.environ.get("MONGO_URI", "mongodb://localhost:27017"),
            database_name=os.environ.get("MONGO_DATABASE_NAME", "social_platform"),
        )


@dataclass(frozen=True, slots=True)
class ApplicationSettings:
    """Aggregate settings for every data store the backend connects to."""

    postgres: PostgresSettings
    redis: RedisSettings
    mongo: MongoSettings

    @classmethod
    def from_environment(cls) -> ApplicationSettings:
        """Build every data store's settings from environment variables."""
        return cls(
            postgres=PostgresSettings.from_environment(),
            redis=RedisSettings.from_environment(),
            mongo=MongoSettings.from_environment(),
        )
