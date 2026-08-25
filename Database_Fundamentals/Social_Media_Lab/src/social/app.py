"""Composition root: the only place in the codebase that constructs a concrete infrastructure class directly, wiring the real Postgres/Redis/Mongo implementations to the services."""
from social.cache.redis_cache import RedisCache
from social.config import load_settings
from social.database.connection_pool import PostgresConnectionPool
from social.database.mongo_activity_logger import MongoActivityLogger
from social.database.schema import ensure_schema
from social.database.unit_of_work import PostgresUnitOfWork
from social.repositories.comment_repository import PostgresCommentRepository
from social.repositories.feed_repository import PostgresFeedRepository
from social.repositories.follower_repository import PostgresFollowerRepository
from social.repositories.like_repository import PostgresLikeRepository
from social.repositories.post_repository import PostgresPostRepository
from social.repositories.user_repository import PostgresUserRepository
from social.services.comment_service import CommentService
from social.services.feed_service import FeedService
from social.services.follow_service import FollowService
from social.services.like_service import LikeService
from social.services.post_service import PostService
from social.services.user_service import UserService


class App:
    """Wires concrete infrastructure to services; the only place that does."""

    def __init__(self) -> None:
        """Load settings, ensure the schema exists, and build every service with its concrete dependencies."""
        settings = load_settings()
        pool = PostgresConnectionPool(
            settings.postgres_dsn,
            settings.postgres_pool_min_size,
            settings.postgres_pool_max_size,
        )
        connection = pool.get_connection()
        try:
            ensure_schema(connection)
        finally:
            pool.release_connection(connection)

        cache = RedisCache(settings.redis_url)
        activity_logger = MongoActivityLogger(settings.mongo_uri, settings.mongo_db_name)

        def uow_factory() -> PostgresUnitOfWork:
            return PostgresUnitOfWork(pool)

        self.users = UserService(uow_factory, PostgresUserRepository(), activity_logger)
        self.posts = PostService(uow_factory, PostgresPostRepository(), activity_logger)
        self.comments = CommentService(uow_factory, PostgresCommentRepository(), activity_logger)
        self.follows = FollowService(
            uow_factory, PostgresFollowerRepository(), activity_logger, cache
        )
        self.likes = LikeService(uow_factory, PostgresLikeRepository(), activity_logger)
        self.feed = FeedService(
            uow_factory, PostgresFeedRepository(), cache, settings.redis_timeline_ttl_seconds
        )
