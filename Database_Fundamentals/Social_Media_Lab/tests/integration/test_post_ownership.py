"""Integration tests for post ownership enforcement against real PostgreSQL.

A mocked repository would happily let an unscoped UPDATE/DELETE through; these prove the
real `WHERE post_id = ... AND author_user_id = ...` clause actually rejects non-owners.
"""

from __future__ import annotations

from typing import Any

import pytest
from pymongo.database import Database

from social_platform.common.exceptions import OwnershipError, PostNotFoundError
from social_platform.common.postgres_pool import PostgresConnectionPool
from social_platform.features.activity_log.repository import MongoActivityLogRepository
from social_platform.features.posts.repository import PostgresPostRepository
from social_platform.features.posts.service import PostService
from social_platform.features.tags.repository import PostgresTagRepository
from social_platform.features.users.model import User

pytestmark = pytest.mark.integration


def _make_service(
    connection_pool: PostgresConnectionPool, mongo_database: Database[dict[str, Any]]
) -> PostService:
    return PostService(
        PostgresPostRepository(connection_pool),
        PostgresTagRepository(connection_pool),
        MongoActivityLogRepository(mongo_database),
    )


def test_update_post_rejects_a_non_owner(
    connection_pool: PostgresConnectionPool,
    mongo_database: Database[dict[str, Any]],
    existing_users: tuple[User, User],
) -> None:
    """A user cannot edit another user's post, even with a valid post id."""
    author, other_user = existing_users
    service = _make_service(connection_pool, mongo_database)
    post = service.create_post(author.user_id, "original content")

    with pytest.raises(OwnershipError):
        service.update_post(post.post_id, other_user.user_id, "hijacked content")


def test_delete_post_rejects_a_non_owner(
    connection_pool: PostgresConnectionPool,
    mongo_database: Database[dict[str, Any]],
    existing_users: tuple[User, User],
) -> None:
    """A user cannot delete another user's post, even with a valid post id."""
    author, other_user = existing_users
    service = _make_service(connection_pool, mongo_database)
    post = service.create_post(author.user_id, "original content")

    with pytest.raises(OwnershipError):
        service.delete_post(post.post_id, other_user.user_id)

    assert service.get_posts_by_author(author.user_id)


def test_update_post_and_delete_post_succeed_for_the_real_owner(
    connection_pool: PostgresConnectionPool,
    mongo_database: Database[dict[str, Any]],
    existing_users: tuple[User, User],
) -> None:
    """The actual author can edit and then delete their own post."""
    author, _ = existing_users
    service = _make_service(connection_pool, mongo_database)
    post = service.create_post(author.user_id, "original content")

    updated_post = service.update_post(post.post_id, author.user_id, "edited content")
    assert updated_post.content == "edited content"

    service.delete_post(post.post_id, author.user_id)
    assert service.get_posts_by_author(author.user_id) == []


def test_update_post_on_a_nonexistent_post_raises_post_not_found(
    connection_pool: PostgresConnectionPool,
    mongo_database: Database[dict[str, Any]],
    existing_users: tuple[User, User],
) -> None:
    """Updating a post id that was never created is a not-found, not an ownership error."""
    author, _ = existing_users
    service = _make_service(connection_pool, mongo_database)

    with pytest.raises(PostNotFoundError):
        service.update_post(999_999, author.user_id, "edited content")
