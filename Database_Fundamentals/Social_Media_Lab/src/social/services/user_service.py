"""Registering a user is one atomic transaction; the activity log write
happens only after that transaction has committed, outside the ACID boundary.
"""
from typing import Callable, Optional, Sequence

from social.interfaces import ActivityLogger, UnitOfWork, UserRepository
from social.models import User
from social.utils.password_hashing import hash_password, verify_password


class UserService:
    """Registers users, updates their profiles, and authenticates them, logging account events to the activity log after commit."""

    def __init__(
        self,
        unit_of_work_factory: Callable[[], UnitOfWork],
        user_repository: UserRepository,
        activity_logger: ActivityLogger,
    ) -> None:
        """Store the unit-of-work factory, user repository, and activity logger used by this service."""
        self._unit_of_work_factory = unit_of_work_factory
        self._user_repository = user_repository
        self._activity_logger = activity_logger

    def register(
        self, username: str, email: str, password: str, full_name: str = "", bio: str = ""
    ) -> User:
        """Register a new user with a hashed password and log the registration event after the transaction commits."""
        draft = User(
            id=None,
            username=username,
            email=email,
            password_hash=hash_password(password),
            full_name=full_name,
            bio=bio,
        )
        with self._unit_of_work_factory() as uow:
            created = self._user_repository.create(uow.cursor, draft)
            uow.commit()

        self._activity_logger.log(
            "user_registered",
            {"user_id": created.id, "username": username},
        )
        return created

    def update_profile(self, user_id: int, full_name: str, bio: str) -> User:
        """Update a user's profile and log the update event after the transaction commits."""
        with self._unit_of_work_factory() as uow:
            updated = self._user_repository.update_profile(uow.cursor, user_id, full_name, bio)
            uow.commit()

        self._activity_logger.log(
            "profile_updated",
            {"user_id": user_id},
        )
        return updated

    def authenticate(self, email: str, password: str) -> Optional[User]:
        """Return the user matching the given email if the password verifies, otherwise None."""
        with self._unit_of_work_factory() as uow:
            user = self._user_repository.get_by_email(uow.cursor, email)
        if user is None or not verify_password(password, user.password_hash):
            return None
        return user

    def find_by_username(self, username: str) -> Optional[User]:
        """Return the user with the given username, if any."""
        with self._unit_of_work_factory() as uow:
            return self._user_repository.get_by_username(uow.cursor, username)

    def list_users(self) -> Sequence[User]:
        """Return all registered users."""
        with self._unit_of_work_factory() as uow:
            return self._user_repository.list_all(uow.cursor)
