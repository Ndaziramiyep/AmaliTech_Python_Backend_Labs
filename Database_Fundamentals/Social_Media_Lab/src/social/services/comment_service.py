"""Creating a comment is one atomic transaction; the activity log write
happens only after that transaction has committed, outside the ACID boundary.
"""
from typing import Callable, Sequence

from social.domain.interfaces import ActivityLogger, CommentRepository, UnitOfWork
from social.domain.models import Comment


class CommentService:
    def __init__(
        self,
        unit_of_work_factory: Callable[[], UnitOfWork],
        comment_repository: CommentRepository,
        activity_logger: ActivityLogger,
    ) -> None:
        self._unit_of_work_factory = unit_of_work_factory
        self._comment_repository = comment_repository
        self._activity_logger = activity_logger

    def create_comment(self, post_id: int, author_id: int, body: str) -> Comment:
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
        with self._unit_of_work_factory() as uow:
            return self._comment_repository.list_by_post(uow.cursor, post_id)
