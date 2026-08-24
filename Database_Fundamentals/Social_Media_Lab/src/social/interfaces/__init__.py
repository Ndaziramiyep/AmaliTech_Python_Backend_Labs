"""Protocols implemented by concrete infrastructure/repositories, re-exported here for convenient imports."""
from social.interfaces.activity_logger import ActivityLogger
from social.interfaces.cache import Cache
from social.interfaces.repositories import (
    CommentRepository,
    FeedRepository,
    FollowerRepository,
    LikeRepository,
    PostRepository,
    UserRepository,
)
from social.interfaces.unit_of_work import UnitOfWork

__all__ = [
    "ActivityLogger",
    "Cache",
    "CommentRepository",
    "FeedRepository",
    "FollowerRepository",
    "LikeRepository",
    "PostRepository",
    "UnitOfWork",
    "UserRepository",
]
