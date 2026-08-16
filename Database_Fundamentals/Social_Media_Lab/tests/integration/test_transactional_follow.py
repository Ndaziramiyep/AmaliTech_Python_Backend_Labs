"""Integration tests for the transactional follow/unfollow contract against real PostgreSQL.

These cover exactly the edge cases a mocked cursor cannot verify: a real CHECK-constraint
rejection, a real foreign-key violation, and real ON CONFLICT/idempotency behavior.
"""

from __future__ import annotations

from typing import Any

import pytest
from pymongo.database import Database

from social_platform.common.exceptions import InvalidFollowOperationError, UserNotFoundError
from social_platform.common.postgres_pool import PostgresConnectionPool
from social_platform.features.activity_log.repository import MongoActivityLogRepository
from social_platform.features.followers.model import FollowResult, UnfollowResult
from social_platform.features.followers.repository import PostgresFollowerRepository
from social_platform.features.followers.service import FollowService
from social_platform.features.users.model import User

pytestmark = pytest.mark.integration


def _make_service(
    connection_pool: PostgresConnectionPool, mongo_database: Database[dict[str, Any]]
) -> FollowService:
    return FollowService(
        PostgresFollowerRepository(connection_pool),
        MongoActivityLogRepository(mongo_database),
    )


def test_follow_user_rejects_self_follow_before_hitting_the_check_constraint(
    connection_pool: PostgresConnectionPool,
    mongo_database: Database[dict[str, Any]],
    existing_users: tuple[User, User],
) -> None:
    """A self-follow is rejected as a domain error, never surfacing as a raw CHECK violation."""
    first_user, _ = existing_users
    service = _make_service(connection_pool, mongo_database)

    with pytest.raises(InvalidFollowOperationError):
        service.follow_user(first_user.user_id, first_user.user_id)


def test_follow_user_translates_a_real_foreign_key_violation(
    connection_pool: PostgresConnectionPool,
    mongo_database: Database[dict[str, Any]],
    existing_users: tuple[User, User],
) -> None:
    """Following a nonexistent user surfaces as UserNotFoundError, not psycopg2's raw error."""
    first_user, _ = existing_users
    service = _make_service(connection_pool, mongo_database)

    with pytest.raises(UserNotFoundError):
        service.follow_user(first_user.user_id, 999_999)


def test_following_the_same_user_twice_is_idempotent(
    connection_pool: PostgresConnectionPool,
    mongo_database: Database[dict[str, Any]],
    existing_users: tuple[User, User],
) -> None:
    """A duplicate follow reports ALREADY_EXISTS instead of raising a unique-violation."""
    first_user, second_user = existing_users
    service = _make_service(connection_pool, mongo_database)

    first_result = service.follow_user(first_user.user_id, second_user.user_id)
    second_result = service.follow_user(first_user.user_id, second_user.user_id)

    assert first_result is FollowResult.CREATED
    assert second_result is FollowResult.ALREADY_EXISTS


def test_unfollowing_a_user_not_followed_is_idempotent(
    connection_pool: PostgresConnectionPool,
    mongo_database: Database[dict[str, Any]],
    existing_users: tuple[User, User],
) -> None:
    """Unfollowing an edge that was never created reports DID_NOT_EXIST, not an error."""
    first_user, second_user = existing_users
    service = _make_service(connection_pool, mongo_database)

    result = service.unfollow_user(first_user.user_id, second_user.user_id)

    assert result is UnfollowResult.DID_NOT_EXIST


def test_follow_then_unfollow_removes_the_real_row(
    connection_pool: PostgresConnectionPool,
    mongo_database: Database[dict[str, Any]],
    existing_users: tuple[User, User],
) -> None:
    """A follow followed by an unfollow actually deletes the row from PostgreSQL."""
    first_user, second_user = existing_users
    service = _make_service(connection_pool, mongo_database)

    service.follow_user(first_user.user_id, second_user.user_id)
    result = service.unfollow_user(first_user.user_id, second_user.user_id)

    assert result is UnfollowResult.REMOVED
    assert (
        service.unfollow_user(first_user.user_id, second_user.user_id)
        is UnfollowResult.DID_NOT_EXIST
    )


def test_follow_user_records_a_mongo_activity_event_after_commit(
    connection_pool: PostgresConnectionPool,
    mongo_database: Database[dict[str, Any]],
    existing_users: tuple[User, User],
) -> None:
    """A successful follow leaves exactly one user_followed document in MongoDB."""
    first_user, second_user = existing_users
    service = _make_service(connection_pool, mongo_database)

    service.follow_user(first_user.user_id, second_user.user_id)

    documents = list(mongo_database["activity_logs"].find({"event_type": "user_followed"}))
    assert len(documents) == 1
