"""Composition root: wires the real Postgres/Redis/Mongo implementations to
the services and exposes them as CLI subcommands.
"""
import argparse
import json
import sys

from social.cli import interactive
from social.config import load_settings
from social.infrastructure.activity.mongo_activity_logger import MongoActivityLogger
from social.infrastructure.cache.redis_client import RedisCache
from social.infrastructure.db.pool import PostgresConnectionPool
from social.infrastructure.db.unit_of_work import PostgresUnitOfWork
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
    def __init__(self) -> None:
        settings = load_settings()
        pool = PostgresConnectionPool(
            settings.postgres_dsn,
            settings.postgres_pool_min_size,
            settings.postgres_pool_max_size,
        )
        uow_factory = lambda: PostgresUnitOfWork(pool)
        cache = RedisCache(settings.redis_url)
        activity_logger = MongoActivityLogger(settings.mongo_uri, settings.mongo_db_name)

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


def main() -> None:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")

    if len(sys.argv) == 1:
        interactive.run(App())
        return

    parser = argparse.ArgumentParser(prog="social-cli")
    sub = parser.add_subparsers(dest="command", required=True)

    register = sub.add_parser("register")
    register.add_argument("username")
    register.add_argument("email")
    register.add_argument("password")

    post = sub.add_parser("post")
    post.add_argument("author_id", type=int)
    post.add_argument("body")

    follow = sub.add_parser("follow")
    follow.add_argument("follower_id", type=int)
    follow.add_argument("followee_id", type=int)

    like = sub.add_parser("like")
    like.add_argument("user_id", type=int)
    like.add_argument("post_id", type=int)

    comment = sub.add_parser("comment")
    comment.add_argument("post_id", type=int)
    comment.add_argument("author_id", type=int)
    comment.add_argument("body")

    timeline = sub.add_parser("timeline")
    timeline.add_argument("user_id", type=int)

    args = parser.parse_args()
    app = App()

    if args.command == "register":
        print(app.users.register(args.username, args.email, args.password))
    elif args.command == "post":
        print(app.posts.create_post(args.author_id, args.body))
    elif args.command == "follow":
        print(app.follows.follow(args.follower_id, args.followee_id))
    elif args.command == "like":
        print(app.likes.like(args.user_id, args.post_id))
    elif args.command == "comment":
        print(app.comments.create_comment(args.post_id, args.author_id, args.body))
    elif args.command == "timeline":
        posts = app.feed.get_timeline(args.user_id)
        print(json.dumps([p.body for p in posts], indent=2))


if __name__ == "__main__":
    main()
