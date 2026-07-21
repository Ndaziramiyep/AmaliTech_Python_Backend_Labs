from abc import ABC, abstractmethod
from typing import Optional

from src.auth.models import User


class UserRepository(ABC):
    """Abstract interface for user storage/retrieval."""

    @abstractmethod
    def get_by_email(self, email: str) -> Optional[User]:
        """Return a user by email, or None if not found."""
        pass

    @abstractmethod
    def add(self, user: User) -> None:
        """Add a new user to the repository."""
        pass


class PasswordHasher(ABC):
    """Abstract interface for password hashing and verification."""

    @abstractmethod
    def hash_password(self, password: str) -> str:
        """Return the hashed version of a plain password."""
        pass

    @abstractmethod
    def verify_password(self, password: str, hashed: str) -> bool:
        """Check if a plain password matches the hashed password."""
        pass
