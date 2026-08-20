"""Integration tests for comment ownership enforcement against real PostgreSQL.

Mirrors test_post_ownership.py: proves the real `WHERE comment_id = ... AND
commenter_user_id = ...` clause actually rejects non-owners, not just a mocked one.
"""

from __future__ import annotations

from typing import Any

import pytest
from pymongo.database import Database

from social_platform.common.exceptions import CommentNotFoundError, OwnershipError
from social_platform.common.postgres_pool import PostgresConnectionPool
from social_platform.features.activity_log.repository import MongoActivityLogRepository
from social_platform.features.comments.repository import PostgresCommentRepository
from social_platform.features.comments.service import CommentService
from social_platform.features.posts.repository import PostgresPostRepository
from social_platform.features.posts.service import PostService
from social_platform.features.tags.repository import PostgresTagRepository
from social_platform.features.users.model import User

pytestmark = pytest.mark.integration


def _make_comment_service(
    connection_pool: PostgresConnectionPool, mongo_database: Database[dict[str, Any]]
) -> CommentService:
    return CommentService(
        PostgresCommentRepository(connection_pool),
        MongoActivityLogRepository(mongo_database),
    )


def _make_post_service(
    connection_pool: PostgresConnectionPool, mongo_database: Database[dict[str, Any]]
) -> PostService:
    return PostService(
        PostgresPostRepository(connection_pool),
        PostgresTagRepository(connection_pool),
        MongoActivityLogRepository(mongo_database),
    )


def test_delete_comment_rejects_a_non_owner(
    connection_pool: PostgresConnectionPool,
    mongo_database: Database[dict[str, Any]],
    existing_users: tuple[User, User],
) -> None:
    """A user cannot delete another user's comment, even with a valid comment id."""
    author, commenter = existing_users
    post_service = _make_post_service(connection_pool, mongo_database)
    comment_service = _make_comment_service(connection_pool, mongo_database)
    post = post_service.create_post(author.user_id, "a post to comment on")
    comment = comment_service.create_comment(post.post_id, commenter.user_id, "nice post")

    with pytest.raises(OwnershipError):
        comment_service.delete_comment(comment.comment_id, author.user_id)


def test_delete_comment_succeeds_for_the_real_owner(
    connection_pool: PostgresConnectionPool,
    mongo_database: Database[dict[str, Any]],
    existing_users: tuple[User, User],
) -> None:
    """The actual commenter can delete their own comment."""
    author, commenter = existing_users
    post_service = _make_post_service(connection_pool, mongo_database)
    comment_service = _make_comment_service(connection_pool, mongo_database)
    post = post_service.create_post(author.user_id, "a post to comment on")
    comment = comment_service.create_comment(post.post_id, commenter.user_id, "nice post")

    comment_service.delete_comment(comment.comment_id, commenter.user_id)

    with pytest.raises(CommentNotFoundError):
        comment_service.delete_comment(comment.comment_id, commenter.user_id)


def test_delete_comment_on_a_nonexistent_comment_raises_comment_not_found(
    connection_pool: PostgresConnectionPool,
    mongo_database: Database[dict[str, Any]],
    existing_users: tuple[User, User],
) -> None:
    """Deleting a comment id that was never created is a clean not-found error."""
    commenter, _ = existing_users
    comment_service = _make_comment_service(connection_pool, mongo_database)

    with pytest.raises(CommentNotFoundError):
        comment_service.delete_comment(999_999, commenter.user_id)
