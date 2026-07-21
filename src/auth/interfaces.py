"""Abstract base classes defining the interfaces for the auth module."""

from abc import ABC, abstractmethod
from typing import Optional

from src.auth.models import User


class UserRepository(ABC):
    """Abstract interface for user storage and retrieval.

    Concrete implementations can use any backend (in-memory, SQL, NoSQL, etc.)
    as long as they satisfy this contract.
    """

    @abstractmethod
    def get_by_email(self, email: str) -> Optional[User]:
        """Return a user by email address, or None if not found.

        Args:
            email: The email address to look up.

        Returns:
            The matching User instance, or None if no user exists.
        """

    @abstractmethod
    def add(self, user: User) -> None:
        """Persist a new user to the repository.

        Args:
            user: The User instance to store.
        """


class PasswordHasher(ABC):
    """Abstract interface for password hashing and verification.

    Concrete implementations can use any algorithm (bcrypt, argon2, etc.)
    as long as they satisfy this contract.
    """

    @abstractmethod
    def hash_password(self, password: str) -> str:
        """Return the hashed version of a plain-text password.

        Args:
            password: The plain-text password to hash.

        Returns:
            A hashed string representation of the password.
        """

    @abstractmethod
    def verify_password(self, password: str, hashed: str) -> bool:
        """Check whether a plain-text password matches a stored hash.

        Args:
            password: The plain-text password to check.
            hashed: The previously hashed password to compare against.

        Returns:
            True if the password matches the hash, False otherwise.
        """
