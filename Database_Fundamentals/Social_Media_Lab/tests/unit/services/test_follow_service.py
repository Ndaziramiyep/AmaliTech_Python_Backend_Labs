import pytest

from social.models import Follower
from social.services.follow_service import FollowService
from social.utils.cache_keys import timeline_cache_key

from .fakes import FakeActivityLogger, FakeCache, FakeFollowerRepository, FakeUnitOfWork


class SelfFollowViolation(Exception):
    """Stand-in for the chk_followers_no_self_follow CHECK constraint."""


class DuplicateFollowViolation(Exception):
    """Stand-in for the followers_pkey UNIQUE violation."""


def _make_service(repository, uow, cache=None, logger=None):
    cache = cache or FakeCache()
    logger = logger or FakeActivityLogger()
    service = FollowService(lambda: uow, repository, logger, cache)
    return service, cache, logger


def test_follow_commits_once_then_logs_activity_and_invalidates_cache():
    repository = FakeFollowerRepository()
    uow = FakeUnitOfWork()
    service, cache, logger = _make_service(repository, uow)

    result = service.follow(follower_id=1, followee_id=2)

    assert result == Follower(follower_id=1, followee_id=2, created_at=None)
    assert repository.calls == [(1, 2)]
    assert repository.received_cursor is uow.cursor
    assert uow.committed is True
    assert uow.rolled_back is False
    assert logger.entries == [("user_followed", {"follower_id": 1, "followee_id": 2})]
    assert cache.deleted_keys == [timeline_cache_key(1)]


@pytest.mark.parametrize(
    "error",
    [SelfFollowViolation("chk_followers_no_self_follow"), DuplicateFollowViolation("followers_pkey")],
)
def test_follow_rolls_back_and_leaves_no_side_effects_when_insert_fails(error):
    repository = FakeFollowerRepository(raise_error=error)
    uow = FakeUnitOfWork()
    service, cache, logger = _make_service(repository, uow)

    with pytest.raises(type(error)):
        service.follow(follower_id=1, followee_id=1)

    assert uow.committed is False
    assert uow.rolled_back is True
    assert logger.entries == []
    assert cache.deleted_keys == []
