"""Registering a user is one atomic transaction; the activity log write
happens only after that transaction has committed, outside the ACID boundary.
"""
from typing import Callable

from social.domain.interfaces import ActivityLogger, UnitOfWork, UserRepository
from social.domain.models import User


class UserService:
    def __init__(
        self,
        unit_of_work_factory: Callable[[], UnitOfWork],
        user_repository: UserRepository,
        activity_logger: ActivityLogger,
    ) -> None:
        self._unit_of_work_factory = unit_of_work_factory
        self._user_repository = user_repository
        self._activity_logger = activity_logger

    def register(self, username: str, email: str) -> User:
        draft = User(id=None, username=username, email=email)
        with self._unit_of_work_factory() as uow:
            created = self._user_repository.create(uow.cursor, draft)
            uow.commit()

        self._activity_logger.log(
            "user_registered",
            {"user_id": created.id, "username": username},
        )
        return created
