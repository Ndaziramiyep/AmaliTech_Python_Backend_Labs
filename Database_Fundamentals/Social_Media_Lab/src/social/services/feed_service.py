"""Reads a follower's timeline cache-aside, keyed by follower id, where FollowService invalidates the entry on new follows but new posts do not, leaving the TTL to bound that staleness."""
import json
from datetime import datetime
from typing import Callable, Sequence

from social.interfaces import Cache, FeedRepository, UnitOfWork
from social.models import Post
from social.utils.cache_keys import timeline_cache_key


class FeedService:
    """Serves a follower's timeline reads from cache, falling back to the repository on a miss."""

    def __init__(
        self,
        unit_of_work_factory: Callable[[], UnitOfWork],
        feed_repository: FeedRepository,
        cache: Cache,
        ttl_seconds: int,
    ) -> None:
        """Store the unit-of-work factory, feed repository, cache, and cache TTL used by this service."""
        self._unit_of_work_factory = unit_of_work_factory
        self._feed_repository = feed_repository
        self._cache = cache
        self._ttl_seconds = ttl_seconds

    def get_timeline(self, follower_id: int, limit: int = 20) -> Sequence[Post]:
        """Return a follower's timeline, serving it from cache when a sufficiently-limited entry exists and otherwise querying and caching it."""
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
    """Convert a Post into a JSON-serializable dict for caching."""
    return {
        "id": post.id,
        "author_id": post.author_id,
        "body": post.body,
        "metadata": post.metadata,
        "created_at": post.created_at.isoformat() if post.created_at else None,
    }


def _post_from_dict(entry: dict) -> Post:
    """Reconstruct a Post from the dict produced by _post_to_dict."""
    return Post(
        id=entry["id"],
        author_id=entry["author_id"],
        body=entry["body"],
        metadata=entry["metadata"],
        created_at=datetime.fromisoformat(entry["created_at"]) if entry["created_at"] else None,
    )
