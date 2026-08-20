"""Fixtures exposing fresh fake repositories to every service unit test."""

from __future__ import annotations

import pytest

from tests.unit.services._fakes import (
    FakeActivityLogRepository,
    FakeCommentRepository,
    FakeFeedRepository,
    FakeFollowerRepository,
    FakeLikeRepository,
    FakePostRepository,
    FakeTagRepository,
    FakeTimelineCache,
    FakeTrendingRepository,
    FakeUserRepository,
)


@pytest.fixture
def fake_user_repository() -> FakeUserRepository:
    """A fresh in-memory user repository."""
    return FakeUserRepository()


@pytest.fixture
def fake_post_repository() -> FakePostRepository:
    """A fresh in-memory post repository."""
    return FakePostRepository()


@pytest.fixture
def fake_comment_repository() -> FakeCommentRepository:
    """A fresh in-memory comment repository."""
    return FakeCommentRepository()


@pytest.fixture
def fake_follower_repository() -> FakeFollowerRepository:
    """A fresh in-memory follower repository."""
    return FakeFollowerRepository()


@pytest.fixture
def fake_tag_repository() -> FakeTagRepository:
    """A fresh in-memory tag repository."""
    return FakeTagRepository()


@pytest.fixture
def fake_like_repository() -> FakeLikeRepository:
    """A fresh in-memory like repository."""
    return FakeLikeRepository()


@pytest.fixture
def fake_feed_repository() -> FakeFeedRepository:
    """A fresh in-memory feed repository."""
    return FakeFeedRepository()


@pytest.fixture
def fake_trending_repository() -> FakeTrendingRepository:
    """A fresh in-memory trending repository."""
    return FakeTrendingRepository()


@pytest.fixture
def fake_timeline_cache() -> FakeTimelineCache:
    """A fresh in-memory timeline cache."""
    return FakeTimelineCache()


@pytest.fixture
def fake_activity_log_repository() -> FakeActivityLogRepository:
    """A fresh in-memory activity log repository."""
    return FakeActivityLogRepository()
