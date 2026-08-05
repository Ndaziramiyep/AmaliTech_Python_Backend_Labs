"""Shared composition-root plumbing: wires concrete repositories from application settings."""

from __future__ import annotations

from dataclasses import dataclass

from social_platform.config.application_settings import ApplicationSettings
from social_platform.database.mongo_connection_factory import create_mongo_database
from social_platform.database.postgres_connection_pool import PostgresConnectionPool
from social_platform.database.redis_connection_factory import create_redis_client
from social_platform.repositories.interfaces import (
    ActivityLogRepositoryInterface,
    CommentRepositoryInterface,
    FollowerRepositoryInterface,
    PostRepositoryInterface,
    TimelineCacheRepositoryInterface,
    UserRepositoryInterface,
)
from social_platform.repositories.mongo_activity_log_repository import (
    MongoActivityLogRepository,
)
from social_platform.repositories.postgres_comment_repository import (
    PostgresCommentRepository,
)
from social_platform.repositories.postgres_follower_repository import (
    PostgresFollowerRepository,
)
from social_platform.repositories.postgres_post_repository import PostgresPostRepository
from social_platform.repositories.postgres_user_repository import PostgresUserRepository
from social_platform.repositories.redis_timeline_cache_repository import (
    RedisTimelineCacheRepository,
)


@dataclass(frozen=True, slots=True)
class RepositoryBundle:
    """Every repository a CLI command might need, exposed by interface (DIP) for testability."""

    user_repository: UserRepositoryInterface
    post_repository: PostRepositoryInterface
    comment_repository: CommentRepositoryInterface
    follower_repository: FollowerRepositoryInterface
    timeline_cache_repository: TimelineCacheRepositoryInterface
    activity_log_repository: ActivityLogRepositoryInterface
    connection_pool: PostgresConnectionPool


def build_repository_bundle() -> RepositoryBundle:
    """Load settings from the environment and wire every concrete repository."""
    settings = ApplicationSettings.from_environment()
    connection_pool = PostgresConnectionPool(settings.postgres)
    redis_client = create_redis_client(settings.redis)
    mongo_database = create_mongo_database(settings.mongo)

    return RepositoryBundle(
        user_repository=PostgresUserRepository(connection_pool),
        post_repository=PostgresPostRepository(connection_pool),
        comment_repository=PostgresCommentRepository(connection_pool),
        follower_repository=PostgresFollowerRepository(connection_pool),
        timeline_cache_repository=RedisTimelineCacheRepository(
            redis_client, settings.redis.timeline_cache_ttl_seconds
        ),
        activity_log_repository=MongoActivityLogRepository(mongo_database),
        connection_pool=connection_pool,
    )
