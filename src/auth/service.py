"""UserService module providing core authentication business logic."""

import logging

from src.auth.exceptions import (
    InvalidPasswordError,
    UserAlreadyExistsError,
    UserNotFoundError,
)
from src.auth.interfaces import PasswordHasher, UserRepository
from src.auth.models import User

logger = logging.getLogger(__name__)


class UserService:
    """Core authentication service for user registration and login.

    Depends on abstractions (UserRepository, PasswordHasher) injected at
    construction time, making it fully testable without real infrastructure.

    Args:
        user_repository: Storage backend implementing UserRepository.
        password_hasher: Hashing backend implementing PasswordHasher.

    Example:
        >>> service = UserService(repo, hasher)
        >>> user = service.register_user("Patrick", "patrick@example.com", "Patrick")
        >>> service.verify_user("patrick@example.com", "Patrick")
        True
    """

    def __init__(
        self, user_repository: UserRepository, password_hasher: PasswordHasher
    ) -> None:
        self._repo = user_repository
        self._hasher = password_hasher
        self._min_password_length = 7

    def register_user(self, username: str, email: str, password: str) -> User:
        """Register a new user with a hashed password.

        Args:
            username: Display name for the user.
            email: Unique email address used as the login identifier.
            password: Plain-text password (must be at least 7 characters).

        Returns:
            The newly created User instance with a generated UUID.

        Raises:
            UserAlreadyExistsError: If a user with the given email already exists.
            InvalidPasswordError: If the password is shorter than 7 characters.

        Example:
            >>> user = service.register_user(
            ...     "Patrick", "patrick@example.com", "Patrick"
            ... )
            >>> print(user.username)
            Patrick
        """
        existing_user = self._repo.get_by_email(email)
        if existing_user:
            raise UserAlreadyExistsError(f"User with email '{email}' already exists.")

        if len(password) < self._min_password_length:
            raise InvalidPasswordError(
                f"Password must be at least {self._min_password_length} characters."
            )

        password_hash = self._hasher.hash_password(password)
        user = User(username=username, email=email, password_hash=password_hash)
        self._repo.add(user)
        logger.info("User registered", extra={"email": user.email})
        return user

    def verify_user(self, email: str, password: str) -> bool:
        """Verify user credentials for login.

        Args:
            email: The email address of the user attempting to log in.
            password: The plain-text password to verify.

        Returns:
            True if credentials are valid.

        Raises:
            UserNotFoundError: If no user exists with the given email.
            InvalidPasswordError: If the password does not match the stored hash.

        Example:
            >>> service.verify_user("patrick@example.com", "Patrick")
            True
        """
        user = self._repo.get_by_email(email)
        if not user:
            logger.info("User login failed: email not found", extra={"email": email})
            raise UserNotFoundError(f"No user found with email '{email}'.")

        if not self._hasher.verify_password(password, user.password_hash):
            logger.info("User login failed: invalid password", extra={"email": email})
            raise InvalidPasswordError("Invalid password.")

        logger.info("User login success", extra={"email": email})
        return True
