"""Abstract interfaces for the auth module."""

from abc import ABC, abstractmethod
from typing import Optional

from src.auth.models import User


class UserRepository(ABC):
    """Interface for user storage and retrieval (in-memory)."""

    @abstractmethod
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Return the user with the given email, or None if not found."""

    @abstractmethod
    def add_user(self, user: User) -> None:
        """Add a new user."""


class PasswordHasher(ABC):
    """Interface for password hashing and verification (bcrypt)."""

    @abstractmethod
    def hash_password(self, password: str) -> str:
        """Return a hash of password."""

    @abstractmethod
    def verify_password(self, password: str, hashed: str) -> None:
        """Raise InvalidPasswordError if password does not match hashed."""
