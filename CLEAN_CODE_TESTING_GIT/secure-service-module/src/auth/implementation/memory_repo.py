from typing import Optional

from src.auth.interfaces import UserRepository
from src.auth.models import User


class InMemoryUserRepository(UserRepository):
    """
    In-memory implementation of UserRepository.

    This repository is intended for testing and demo purposes.
    Users are stored in a dictionary keyed by email.
    """

    def __init__(self) -> None:
        self._users: dict[str, User] = {}

    def get_by_email(self, email: str) -> Optional[User]:
        return self._users.get(email)

    def add(self, user: User) -> None:
        self._users[user.email] = user
