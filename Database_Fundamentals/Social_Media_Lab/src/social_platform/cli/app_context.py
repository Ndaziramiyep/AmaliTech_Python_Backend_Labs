"""The composition root: wires every concrete repository from environment settings.

This is the only place in the codebase that constructs a Postgres/Redis/Mongo
repository directly -- every feature's service depends on a `Protocol`, never on a
concrete store, so this module is where those two sides meet.
"""

from __future__ import annotations

from dataclasses import dataclass

from social_platform.common.mongo_client import create_mongo_database
from social_platform.common.postgres_pool import PostgresConnectionPool
from social_platform.common.redis_client import create_redis_client
from social_platform.common.settings import ApplicationSettings
from social_platform.features.activity_log.repository import (
    ActivityLogRepository,
    MongoActivityLogRepository,
)
from social_platform.features.comments.repository import (
    CommentRepository,
    PostgresCommentRepository,
)
from social_platform.features.feed.cache import RedisTimelineCache, TimelineCache
from social_platform.features.feed.repository import FeedRepository, PostgresFeedRepository
from social_platform.features.followers.repository import (
    FollowerRepository,
    PostgresFollowerRepository,
)
from social_platform.features.likes.repository import LikeRepository, PostgresLikeRepository
from social_platform.features.posts.repository import PostgresPostRepository, PostRepository
from social_platform.features.tags.repository import PostgresTagRepository, TagRepository
from social_platform.features.trending.repository import (
    PostgresTrendingRepository,
    TrendingRepository,
)
from social_platform.features.users.repository import PostgresUserRepository, UserRepository


@dataclass(frozen=True, slots=True)
class AppContext:
    """Every repository the CLI might need, built once per invocation."""

    connection_pool: PostgresConnectionPool
    user_repository: UserRepository
    post_repository: PostRepository
    tag_repository: TagRepository
    comment_repository: CommentRepository
    follower_repository: FollowerRepository
    like_repository: LikeRepository
    feed_repository: FeedRepository
    trending_repository: TrendingRepository
    timeline_cache: TimelineCache
    activity_log_repository: ActivityLogRepository


def build_app_context() -> AppContext:
    """Load settings from the environment and construct every repository."""
    settings = ApplicationSettings.from_environment()
    connection_pool = PostgresConnectionPool(settings.postgres)
    redis_client = create_redis_client(settings.redis)
    mongo_database = create_mongo_database(settings.mongo)

    return AppContext(
        connection_pool=connection_pool,
        user_repository=PostgresUserRepository(connection_pool),
        post_repository=PostgresPostRepository(connection_pool),
        tag_repository=PostgresTagRepository(connection_pool),
        comment_repository=PostgresCommentRepository(connection_pool),
        follower_repository=PostgresFollowerRepository(connection_pool),
        like_repository=PostgresLikeRepository(connection_pool),
        feed_repository=PostgresFeedRepository(connection_pool),
        trending_repository=PostgresTrendingRepository(connection_pool),
        timeline_cache=RedisTimelineCache(redis_client, settings.redis.timeline_cache_ttl_seconds),
        activity_log_repository=MongoActivityLogRepository(mongo_database),
    )
