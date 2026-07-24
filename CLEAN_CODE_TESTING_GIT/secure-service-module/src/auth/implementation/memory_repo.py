"""InMemoryUserRepository -- in-memory implementation of UserRepository."""

from typing import Optional

from src.auth.interfaces import UserRepository
from src.auth.models import User


class InMemoryUserRepository(UserRepository):
    """In-memory implementation of UserRepository.

    Stores users in a plain Python dictionary keyed by email address.
    Intended for testing and demo purposes; not suitable for production use.

    Example:
        >>> repo = InMemoryUserRepository()
        >>> user = User(username="Patrick", email="patrick@gmail.com", password_hash="h")
        >>> repo.add(user)
        >>> repo.get_by_email("patrick@gmail.com") == user
        True
    """

    def __init__(self) -> None:
        self._users: dict[str, User] = {}

    def get_by_email(self, email: str) -> Optional[User]:
        """Return a user by email address, or None if not found.

        Args:
            email: The email address to look up.

        Returns:
            The matching User instance, or None.
        """
        return self._users.get(email)

    def add(self, user: User) -> None:
        """Store a user in the in-memory dictionary.

        Args:
            user: The User instance to persist.
        """
        self._users[user.email] = user
