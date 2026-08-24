"""Creating a comment is one atomic transaction; the activity log write
happens only after that transaction has committed, outside the ACID boundary.
"""
from typing import Callable, Mapping, Sequence

from social.interfaces import ActivityLogger, CommentRepository, UnitOfWork
from social.models import Comment


class CommentService:
    """Creates and queries comments, logging comment creation to the activity log after commit."""

    def __init__(
        self,
        unit_of_work_factory: Callable[[], UnitOfWork],
        comment_repository: CommentRepository,
        activity_logger: ActivityLogger,
    ) -> None:
        """Store the unit-of-work factory, comment repository, and activity logger used by this service."""
        self._unit_of_work_factory = unit_of_work_factory
        self._comment_repository = comment_repository
        self._activity_logger = activity_logger

    def create_comment(self, post_id: int, author_id: int, body: str) -> Comment:
        """Create a comment for a post and log the creation event after the transaction commits."""
        draft = Comment(id=None, post_id=post_id, author_id=author_id, body=body)
        with self._unit_of_work_factory() as uow:
            created = self._comment_repository.create(uow.cursor, draft)
            uow.commit()

        self._activity_logger.log(
            "comment_created",
            {"comment_id": created.id, "post_id": post_id, "author_id": author_id},
        )
        return created

    def list_comments(self, post_id: int) -> Sequence[Comment]:
        """Return all comments for a given post."""
        with self._unit_of_work_factory() as uow:
            return self._comment_repository.list_by_post(uow.cursor, post_id)

    def count_by_posts(self, post_ids: Sequence[int]) -> Mapping[int, int]:
        """Comment count per post id; a post with no comments is simply
        absent."""
        with self._unit_of_work_factory() as uow:
            return self._comment_repository.count_by_posts(uow.cursor, post_ids)
