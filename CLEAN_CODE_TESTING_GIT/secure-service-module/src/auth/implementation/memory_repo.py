"""InMemoryUserRepository -- in-memory UserRepository."""

from typing import Optional

from src.auth.interfaces import UserRepository
from src.auth.models import User


class InMemoryUserRepository(UserRepository):
    """Stores users in a dict keyed by email. For tests/demos only."""

    def __init__(self) -> None:
        self._users: dict[str, User] = {}

    def get_user_by_email(self, email: str) -> Optional[User]:
        return self._users.get(email)

    def add_user(self, user: User) -> None:
        self._users[user.email] = user
