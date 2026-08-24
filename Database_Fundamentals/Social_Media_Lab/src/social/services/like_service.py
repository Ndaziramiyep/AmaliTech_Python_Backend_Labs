"""Liking a post is one atomic transaction; the activity log write happens
only after that transaction has committed, outside the ACID boundary.
"""
from typing import Callable, Mapping, Sequence

from social.interfaces import ActivityLogger, LikeRepository, UnitOfWork
from social.models import Like


class LikeService:
    """Creates likes on posts, logging the like event to the activity log after commit."""

    def __init__(
        self,
        unit_of_work_factory: Callable[[], UnitOfWork],
        like_repository: LikeRepository,
        activity_logger: ActivityLogger,
    ) -> None:
        """Store the unit-of-work factory, like repository, and activity logger used by this service."""
        self._unit_of_work_factory = unit_of_work_factory
        self._like_repository = like_repository
        self._activity_logger = activity_logger

    def like(self, user_id: int, post_id: int) -> Like:
        """Create a like for a post and log the event after the transaction commits."""
        with self._unit_of_work_factory() as uow:
            like = self._like_repository.create(uow.cursor, user_id, post_id)
            uow.commit()

        self._activity_logger.log(
            "post_liked",
            {"user_id": user_id, "post_id": post_id},
        )
        return like

    def count_by_posts(self, post_ids: Sequence[int]) -> Mapping[int, int]:
        """Like count per post id; a post with no likes is simply absent."""
        with self._unit_of_work_factory() as uow:
            return self._like_repository.count_by_posts(uow.cursor, post_ids)
