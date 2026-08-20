"""Integration tests for like/unlike idempotency against real PostgreSQL and MongoDB.

Covers exactly what a mocked cursor cannot: a real `ON CONFLICT DO NOTHING` no-op on a
repeat like, and a real zero-row DELETE no-op on an unlike that never existed.
"""

from __future__ import annotations

from typing import Any

import pytest
from pymongo.database import Database

from social_platform.common.exceptions import PostNotFoundError
from social_platform.common.postgres_pool import PostgresConnectionPool
from social_platform.features.activity_log.repository import MongoActivityLogRepository
from social_platform.features.likes.model import LikeResult, UnlikeResult
from social_platform.features.likes.repository import PostgresLikeRepository
from social_platform.features.likes.service import LikeService
from social_platform.features.posts.repository import PostgresPostRepository
from social_platform.features.posts.service import PostService
from social_platform.features.tags.repository import PostgresTagRepository
from social_platform.features.users.model import User

pytestmark = pytest.mark.integration


def _make_like_service(
    connection_pool: PostgresConnectionPool, mongo_database: Database[dict[str, Any]]
) -> LikeService:
    return LikeService(
        PostgresPostRepository(connection_pool),
        PostgresLikeRepository(connection_pool),
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


def test_liking_the_same_post_twice_is_idempotent(
    connection_pool: PostgresConnectionPool,
    mongo_database: Database[dict[str, Any]],
    existing_users: tuple[User, User],
) -> None:
    """A duplicate like reports ALREADY_EXISTS instead of raising a unique-violation."""
    author, liker = existing_users
    post_service = _make_post_service(connection_pool, mongo_database)
    like_service = _make_like_service(connection_pool, mongo_database)
    post = post_service.create_post(author.user_id, "a likeable post")

    first_result = like_service.like_post(liker.user_id, post.post_id)
    second_result = like_service.like_post(liker.user_id, post.post_id)

    assert first_result is LikeResult.CREATED
    assert second_result is LikeResult.ALREADY_EXISTS


def test_unliking_a_post_never_liked_is_idempotent(
    connection_pool: PostgresConnectionPool,
    mongo_database: Database[dict[str, Any]],
    existing_users: tuple[User, User],
) -> None:
    """Unliking an edge that was never created reports DID_NOT_EXIST, not an error."""
    author, liker = existing_users
    post_service = _make_post_service(connection_pool, mongo_database)
    like_service = _make_like_service(connection_pool, mongo_database)
    post = post_service.create_post(author.user_id, "a post nobody liked")

    result = like_service.unlike_post(liker.user_id, post.post_id)

    assert result is UnlikeResult.DID_NOT_EXIST


def test_like_then_unlike_removes_the_real_row(
    connection_pool: PostgresConnectionPool,
    mongo_database: Database[dict[str, Any]],
    existing_users: tuple[User, User],
) -> None:
    """A like followed by an unlike actually deletes the row, allowing a fresh re-like."""
    author, liker = existing_users
    post_service = _make_post_service(connection_pool, mongo_database)
    like_service = _make_like_service(connection_pool, mongo_database)
    post = post_service.create_post(author.user_id, "a post to like and unlike")

    like_service.like_post(liker.user_id, post.post_id)
    unlike_result = like_service.unlike_post(liker.user_id, post.post_id)
    relike_result = like_service.like_post(liker.user_id, post.post_id)

    assert unlike_result is UnlikeResult.REMOVED
    assert relike_result is LikeResult.CREATED


def test_liking_a_nonexistent_post_raises_post_not_found(
    connection_pool: PostgresConnectionPool,
    mongo_database: Database[dict[str, Any]],
    existing_users: tuple[User, User],
) -> None:
    """Liking a post id that was never created is a clean not-found error."""
    liker, _ = existing_users
    like_service = _make_like_service(connection_pool, mongo_database)

    with pytest.raises(PostNotFoundError):
        like_service.like_post(liker.user_id, 999_999)
