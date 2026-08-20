"""Creating a post is one atomic transaction; the activity log write happens
only after that transaction has committed, outside the ACID boundary.
"""
from typing import Any, Callable, Mapping, Optional, Sequence

from social.domain.interfaces import ActivityLogger, PostRepository, UnitOfWork
from social.domain.models import Post


class PostService:
    def __init__(
        self,
        unit_of_work_factory: Callable[[], UnitOfWork],
        post_repository: PostRepository,
        activity_logger: ActivityLogger,
    ) -> None:
        self._unit_of_work_factory = unit_of_work_factory
        self._post_repository = post_repository
        self._activity_logger = activity_logger

    def create_post(
        self,
        author_id: int,
        body: str,
        metadata: Optional[Mapping[str, Any]] = None,
    ) -> Post:
        draft = Post(id=None, author_id=author_id, body=body, metadata=metadata or {})
        with self._unit_of_work_factory() as uow:
            created = self._post_repository.create(uow.cursor, draft)
            uow.commit()

        self._activity_logger.log(
            "post_created",
            {"post_id": created.id, "author_id": author_id},
        )
        return created

    def list_recent(self, limit: int = 20) -> Sequence[Post]:
        with self._unit_of_work_factory() as uow:
            return self._post_repository.list_recent(uow.cursor, limit)
