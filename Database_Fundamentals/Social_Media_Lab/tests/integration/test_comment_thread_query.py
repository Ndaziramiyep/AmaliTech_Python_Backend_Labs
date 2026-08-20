"""Integration tests for the recursive comment-thread query against real PostgreSQL.

A mocked cursor can't prove a recursive CTE actually walks the self-referencing
`parent_comment_id` adjacency list correctly, or that `ON DELETE CASCADE` really removes
a comment's replies -- these run the real SQL against a real table.
"""

from __future__ import annotations

from typing import Any

import pytest
from pymongo.database import Database

from social_platform.common.exceptions import CommentNotFoundError, InvalidCommentOperationError
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


def test_comment_thread_orders_a_multi_level_reply_chain_depth_first(
    connection_pool: PostgresConnectionPool,
    mongo_database: Database[dict[str, Any]],
    existing_users: tuple[User, User],
) -> None:
    """A reply to a reply comes back immediately after its parent, ahead of later siblings."""
    author, commenter = existing_users
    post_service = _make_post_service(connection_pool, mongo_database)
    comment_service = _make_comment_service(connection_pool, mongo_database)
    post = post_service.create_post(author.user_id, "a post with a deep thread")

    top_level = comment_service.create_comment(post.post_id, commenter.user_id, "top-level")
    reply = comment_service.create_comment(
        post.post_id, author.user_id, "a reply", top_level.comment_id
    )
    comment_service.create_comment(
        post.post_id, commenter.user_id, "a reply to the reply", reply.comment_id
    )
    second_top_level = comment_service.create_comment(
        post.post_id, author.user_id, "another top-level"
    )

    thread = comment_service.get_comment_thread(post.post_id)

    assert [entry.comment.content for entry in thread] == [
        "top-level",
        "a reply",
        "a reply to the reply",
        "another top-level",
    ]
    assert [entry.depth for entry in thread] == [0, 1, 2, 0]
    assert thread[-1].comment.comment_id == second_top_level.comment_id


def test_deleting_a_comment_cascades_to_its_replies(
    connection_pool: PostgresConnectionPool,
    mongo_database: Database[dict[str, Any]],
    existing_users: tuple[User, User],
) -> None:
    """Deleting a top-level comment also removes every reply beneath it (ON DELETE CASCADE)."""
    author, commenter = existing_users
    post_service = _make_post_service(connection_pool, mongo_database)
    comment_service = _make_comment_service(connection_pool, mongo_database)
    post = post_service.create_post(author.user_id, "a post with a thread to delete")

    top_level = comment_service.create_comment(post.post_id, commenter.user_id, "top-level")
    comment_service.create_comment(post.post_id, author.user_id, "a reply", top_level.comment_id)

    comment_service.delete_comment(top_level.comment_id, commenter.user_id)

    assert comment_service.get_comment_thread(post.post_id) == []


def test_replying_to_a_nonexistent_comment_raises_comment_not_found(
    connection_pool: PostgresConnectionPool,
    mongo_database: Database[dict[str, Any]],
    existing_users: tuple[User, User],
) -> None:
    """A reply's parent must actually exist -- a real foreign-key violation, translated."""
    author, commenter = existing_users
    post_service = _make_post_service(connection_pool, mongo_database)
    comment_service = _make_comment_service(connection_pool, mongo_database)
    post = post_service.create_post(author.user_id, "a post")

    with pytest.raises(CommentNotFoundError):
        comment_service.create_comment(post.post_id, commenter.user_id, "a reply", 999_999)


def test_replying_to_a_comment_on_a_different_post_is_rejected(
    connection_pool: PostgresConnectionPool,
    mongo_database: Database[dict[str, Any]],
    existing_users: tuple[User, User],
) -> None:
    """A reply's parent comment must belong to the same post it's replying within."""
    author, commenter = existing_users
    post_service = _make_post_service(connection_pool, mongo_database)
    comment_service = _make_comment_service(connection_pool, mongo_database)
    first_post = post_service.create_post(author.user_id, "first post")
    second_post = post_service.create_post(author.user_id, "second post")
    comment_on_first_post = comment_service.create_comment(
        first_post.post_id, commenter.user_id, "on the first post"
    )

    with pytest.raises(InvalidCommentOperationError):
        comment_service.create_comment(
            second_post.post_id, commenter.user_id, "a reply", comment_on_first_post.comment_id
        )
