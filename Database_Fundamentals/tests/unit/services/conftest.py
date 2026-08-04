"""Fixtures exposing fresh fake repositories to every service unit test."""

from __future__ import annotations

import pytest

from tests.unit.services._fakes import (
    FakeActivityLogRepository,
    FakeCommentRepository,
    FakeFollowerRepository,
    FakePostRepository,
    FakeTimelineCacheRepository,
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
def fake_timeline_cache_repository() -> FakeTimelineCacheRepository:
    """A fresh in-memory timeline cache repository."""
    return FakeTimelineCacheRepository()


@pytest.fixture
def fake_activity_log_repository() -> FakeActivityLogRepository:
    """A fresh in-memory activity log repository."""
    return FakeActivityLogRepository()
