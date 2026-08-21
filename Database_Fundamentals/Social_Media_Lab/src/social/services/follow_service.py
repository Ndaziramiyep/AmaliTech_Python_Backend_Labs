"""Following is one atomic transaction. The activity log write and cache
invalidation are deliberately outside the UnitOfWork: they happen only after
that transaction has committed, and are not part of the ACID boundary.
"""
from typing import Callable, Sequence

from social.domain.interfaces import ActivityLogger, Cache, FollowerRepository, UnitOfWork
from social.domain.models import Follower
from social.services.cache_keys import timeline_cache_key


class FollowService:
    def __init__(
        self,
        unit_of_work_factory: Callable[[], UnitOfWork],
        follower_repository: FollowerRepository,
        activity_logger: ActivityLogger,
        cache: Cache,
    ) -> None:
        self._unit_of_work_factory = unit_of_work_factory
        self._follower_repository = follower_repository
        self._activity_logger = activity_logger
        self._cache = cache

    def follow(self, follower_id: int, followee_id: int) -> Follower:
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
        with self._unit_of_work_factory() as uow:
            return self._follower_repository.list_following(uow.cursor, follower_id)

    def list_followers(self, followee_id: int) -> Sequence[int]:
        with self._unit_of_work_factory() as uow:
            return self._follower_repository.list_followers(uow.cursor, followee_id)
