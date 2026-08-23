"""Protocols implemented by concrete infrastructure/repositories.

Re-exported here so callers can `from social.interfaces import X` instead
of reaching into the individual submodule per protocol.
"""
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
