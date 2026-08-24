"""Following and unfollowing each run as one atomic transaction, with the activity log write and cache invalidation deliberately kept outside the UnitOfWork and performed only after that transaction has committed."""
from typing import Callable, Sequence

from social.interfaces import ActivityLogger, Cache, FollowerRepository, UnitOfWork
from social.models import Follower
from social.utils.cache_keys import timeline_cache_key


class FollowService:
    """Creates, removes, and lists follow relationships between users, invalidating the follower's timeline cache on changes."""

    def __init__(
        self,
        unit_of_work_factory: Callable[[], UnitOfWork],
        follower_repository: FollowerRepository,
        activity_logger: ActivityLogger,
        cache: Cache,
    ) -> None:
        """Store the unit-of-work factory, follower repository, activity logger, and cache used by this service."""
        self._unit_of_work_factory = unit_of_work_factory
        self._follower_repository = follower_repository
        self._activity_logger = activity_logger
        self._cache = cache

    def follow(self, follower_id: int, followee_id: int) -> Follower:
        """Create a follow relationship, log the event, and invalidate the follower's timeline cache after the transaction commits."""
        with self._unit_of_work_factory() as uow:
            follower = self._follower_repository.create(uow.cursor, follower_id, followee_id)
            uow.commit()

        self._activity_logger.log(
            "user_followed",
            {"follower_id": follower_id, "followee_id": followee_id},
        )
        self._cache.delete(timeline_cache_key(follower_id))
        return follower

    def unfollow(self, follower_id: int, followee_id: int) -> bool:
        """Remove a follow relationship, logging the event and invalidating the follower's timeline cache only if a relationship was actually removed."""
        with self._unit_of_work_factory() as uow:
            removed = self._follower_repository.delete(uow.cursor, follower_id, followee_id)
            uow.commit()

        if removed:
            self._activity_logger.log(
                "user_unfollowed",
                {"follower_id": follower_id, "followee_id": followee_id},
            )
            self._cache.delete(timeline_cache_key(follower_id))
        return removed

    def list_following(self, follower_id: int) -> Sequence[int]:
        """Return the ids of the users a given user follows."""
        with self._unit_of_work_factory() as uow:
            return self._follower_repository.list_following(uow.cursor, follower_id)

    def list_followers(self, followee_id: int) -> Sequence[int]:
        """Return the ids of the users following a given user."""
        with self._unit_of_work_factory() as uow:
            return self._follower_repository.list_followers(uow.cursor, followee_id)
