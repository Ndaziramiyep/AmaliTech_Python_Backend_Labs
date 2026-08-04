"""Integration tests for the real CTE + JOIN + ROW_NUMBER() timeline feed query."""

from __future__ import annotations

import pytest

from social_platform.database.postgres_connection_pool import PostgresConnectionPool
from social_platform.models.entities import User
from social_platform.repositories.postgres_follower_repository import (
    PostgresFollowerRepository,
)
from social_platform.repositories.postgres_post_repository import PostgresPostRepository

pytestmark = pytest.mark.integration


def test_feed_only_includes_posts_from_followed_users_newest_first(
    connection_pool: PostgresConnectionPool, existing_users: tuple[User, User]
) -> None:
    """A user's feed excludes posts from users they do not follow, ordered newest first."""
    follower, followee = existing_users
    post_repository = PostgresPostRepository(connection_pool)
    follower_repository = PostgresFollowerRepository(connection_pool)
    follower_repository.create_follow_relationship(follower.user_id, followee.user_id)

    post_repository.create_post(followee.user_id, "first post", {})
    post_repository.create_post(followee.user_id, "second post", {})
    post_repository.create_post(follower.user_id, "a post from myself, not in my own feed", {})

    feed_page = post_repository.fetch_timeline_feed_page(follower.user_id, 1, 20)

    assert [entry.content for entry in feed_page] == ["second post", "first post"]


def test_feed_pagination_splits_results_across_pages_without_overlap(
    connection_pool: PostgresConnectionPool, existing_users: tuple[User, User]
) -> None:
    """Rows 1-2 and rows 3-4 of a five-post feed are disjoint, contiguous pages."""
    follower, followee = existing_users
    post_repository = PostgresPostRepository(connection_pool)
    follower_repository = PostgresFollowerRepository(connection_pool)
    follower_repository.create_follow_relationship(follower.user_id, followee.user_id)
    for post_number in range(5):
        post_repository.create_post(followee.user_id, f"post {post_number}", {})

    first_page = post_repository.fetch_timeline_feed_page(follower.user_id, 1, 2)
    second_page = post_repository.fetch_timeline_feed_page(follower.user_id, 3, 4)

    first_page_ids = {entry.post_id for entry in first_page}
    second_page_ids = {entry.post_id for entry in second_page}
    assert len(first_page) == 2
    assert len(second_page) == 2
    assert first_page_ids.isdisjoint(second_page_ids)
