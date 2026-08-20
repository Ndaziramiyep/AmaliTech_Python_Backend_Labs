from datetime import datetime, timezone

from social.domain.models import Post
from social.services.cache_keys import timeline_cache_key
from social.services.feed_service import FeedService

from .fakes import FakeCache, FakeFeedRepository, FakeUnitOfWork

CREATED_AT = datetime(2026, 1, 1, tzinfo=timezone.utc)


def test_get_timeline_on_cache_miss_queries_repository_then_populates_cache():
    posts = [Post(id=1, author_id=2, body="hi", metadata={}, created_at=CREATED_AT)]
    repository = FakeFeedRepository(posts=posts)
    cache = FakeCache()
    uow = FakeUnitOfWork()
    service = FeedService(lambda: uow, repository, cache, ttl_seconds=60)

    result = service.get_timeline(follower_id=1)

    assert result == posts
    assert repository.calls == [(1, 20)]
    assert cache.get(timeline_cache_key(1)) is not None


def test_get_timeline_on_cache_hit_does_not_query_repository():
    posts = [Post(id=1, author_id=2, body="hi", metadata={}, created_at=CREATED_AT)]
    repository = FakeFeedRepository(posts=posts)
    cache = FakeCache()
    uow = FakeUnitOfWork()
    service = FeedService(lambda: uow, repository, cache, ttl_seconds=60)
    service.get_timeline(follower_id=1)
    repository.calls.clear()

    result = service.get_timeline(follower_id=1)

    assert result == posts
    assert repository.calls == []
