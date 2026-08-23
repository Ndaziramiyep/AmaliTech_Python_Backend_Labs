import pytest

from social.models import Like
from social.services.like_service import LikeService

from .fakes import FakeActivityLogger, FakeLikeRepository, FakeUnitOfWork


class DuplicateLikeViolation(Exception):
    """Stand-in for the likes primary-key UNIQUE violation."""


def test_like_commits_once_then_logs_activity():
    repository = FakeLikeRepository()
    uow = FakeUnitOfWork()
    logger = FakeActivityLogger()
    service = LikeService(lambda: uow, repository, logger)

    result = service.like(user_id=1, post_id=10)

    assert result == Like(user_id=1, post_id=10, created_at=None)
    assert repository.calls == [(1, 10)]
    assert repository.received_cursor is uow.cursor
    assert uow.committed is True
    assert uow.rolled_back is False
    assert logger.entries == [("post_liked", {"user_id": 1, "post_id": 10})]


def test_like_rolls_back_and_leaves_no_side_effects_when_insert_fails():
    error = DuplicateLikeViolation("likes_pkey")
    repository = FakeLikeRepository(raise_error=error)
    uow = FakeUnitOfWork()
    logger = FakeActivityLogger()
    service = LikeService(lambda: uow, repository, logger)

    with pytest.raises(DuplicateLikeViolation):
        service.like(user_id=1, post_id=10)

    assert uow.committed is False
    assert uow.rolled_back is True
    assert logger.entries == []


def test_count_by_posts_returns_per_post_like_counts():
    repository = FakeLikeRepository()
    uow = FakeUnitOfWork()
    logger = FakeActivityLogger()
    service = LikeService(lambda: uow, repository, logger)
    service.like(user_id=1, post_id=10)
    service.like(user_id=2, post_id=10)
    service.like(user_id=1, post_id=20)

    result = service.count_by_posts([10, 20, 30])

    assert result == {10: 2, 20: 1}
    assert 30 not in result
