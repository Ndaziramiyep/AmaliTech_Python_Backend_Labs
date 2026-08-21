"""Cache-aside read of a user's timeline.

FollowService already invalidates timeline_cache_key(follower_id) whenever
a new follow edge is created, so a miss here means either "never cached" or
"invalidated by a follow" - not "stale from a new post" (posts don't
invalidate followers' caches; the TTL bounds that staleness instead).
"""
import json
from datetime import datetime
from typing import Callable, Sequence

from social.domain.interfaces import Cache, FeedRepository, UnitOfWork
from social.domain.models import Post
from social.services.cache_keys import timeline_cache_key


class FeedService:
    def __init__(
        self,
        unit_of_work_factory: Callable[[], UnitOfWork],
        feed_repository: FeedRepository,
        cache: Cache,
        ttl_seconds: int,
    ) -> None:
        self._unit_of_work_factory = unit_of_work_factory
        self._feed_repository = feed_repository
        self._cache = cache
        self._ttl_seconds = ttl_seconds

    def get_timeline(self, follower_id: int, limit: int = 20) -> Sequence[Post]:
        key = timeline_cache_key(follower_id)
        cached = self._cache.get(key)
        if cached is not None:
            payload = json.loads(cached)
            # A cache entry only satisfies a request whose limit it was
            # actually fetched at (or a smaller one) - otherwise a earlier
            # small-limit read would silently cap a later, larger request.
            if payload["limit"] >= limit:
                posts = [_post_from_dict(entry) for entry in payload["posts"]]
                return posts[:limit]

        with self._unit_of_work_factory() as uow:
            posts = self._feed_repository.get_timeline(uow.cursor, follower_id, limit)

        self._cache.set(
            key,
            json.dumps({"limit": limit, "posts": [_post_to_dict(post) for post in posts]}),
            self._ttl_seconds,
        )
        return posts


def _post_to_dict(post: Post) -> dict:
    return {
        "id": post.id,
        "author_id": post.author_id,
        "body": post.body,
        "metadata": post.metadata,
        "created_at": post.created_at.isoformat() if post.created_at else None,
    }


def _post_from_dict(entry: dict) -> Post:
    return Post(
        id=entry["id"],
        author_id=entry["author_id"],
        body=entry["body"],
        metadata=entry["metadata"],
        created_at=datetime.fromisoformat(entry["created_at"]) if entry["created_at"] else None,
    )
