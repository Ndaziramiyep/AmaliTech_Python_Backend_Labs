"""UserService module providing core authentication business logic."""

import logging
import re
import time
from contextlib import contextmanager
from typing import Generator

from src.auth.exceptions import (
    InvalidPasswordError,
    UserAlreadyExistsError,
    UserNotFoundError,
)
from src.auth.interfaces import PasswordHasher, UserRepository
from src.auth.models import User

logger = logging.getLogger(__name__)

_EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _validate_username(username: str) -> None:
    """Raise ValueError if the username is empty or only whitespace.

    Args:
        username: The username to validate.
    """
    if not username or not username.strip():
        raise ValueError("Username must not be empty.")


def _validate_email(email: str) -> None:
    """Raise ValueError if the email address is not well-formed.

    Uses a simple local-part@domain.tld pattern rather than full RFC 5322
    validation; genuine deliverability is confirmed separately (e.g. via a
    confirmation link), not by this format check.

    Args:
        email: The email address to validate.
    """
    if not email or not _EMAIL_PATTERN.match(email):
        raise ValueError(f"'{email}' is not a valid email address.")


class _OperationTimer:
    """Exposes elapsed time in milliseconds for an in-flight operation."""

    def __init__(self) -> None:
        self._start = time.perf_counter()

    @property
    def elapsed_ms(self) -> float:
        """Milliseconds elapsed since the timer was created."""
        return (time.perf_counter() - self._start) * 1000


@contextmanager
def _timed_operation(operation: str) -> Generator[_OperationTimer, None, None]:
    """Time an operation and log its start/finish as structured debug events.

    Used to wrap the auth operations below so their duration is always
    recorded, whether they succeed or raise.

    Args:
        operation: Short name identifying the operation being timed.

    Yields:
        An _OperationTimer exposing the elapsed time so far.
    """
    timer = _OperationTimer()
    logger.debug("%s started", operation)
    try:
        yield timer
    finally:
        logger.debug("%s finished", operation, extra={"duration_ms": timer.elapsed_ms})


class UserService:
    """Core authentication service for user registration and login.

    Depends on abstractions (UserRepository, PasswordHasher) injected at
    construction time, making it fully testable without real infrastructure.

    Args:
        user_repository: Storage backend implementing UserRepository.
        password_hasher: Hashing backend implementing PasswordHasher.

    Example:
        >>> service = UserService(repo, hasher)
        >>> user = service.register_user("Patrick", "patrick@gmail.com", "SecurePass1")
    """

    _MIN_PASSWORD_LENGTH = 8

    def __init__(
        self, user_repository: UserRepository, password_hasher: PasswordHasher
    ) -> None:
        self._repo = user_repository
        self._hasher = password_hasher

    def register_user(self, username: str, email: str, password: str) -> User:
        """Register a new user with a hashed password.

        Args:
            username: Display name for the user.
            email: Unique email address used as the login identifier.
            password: Plain-text password (must be at least 8 characters).

        Returns:
            The newly created User instance with a generated UUID.

        Raises:
            ValueError: If the username is blank or the email is malformed.
            UserAlreadyExistsError: If a user with the given email already exists.
            InvalidPasswordError: If the password is shorter than 8 characters.
        """
        _validate_username(username)
        _validate_email(email)

        with _timed_operation("register_user"):
            if self._repo.get_by_email(email):
                raise UserAlreadyExistsError(
                    f"User with email '{email}' already exists."
                )

            if len(password) < self._MIN_PASSWORD_LENGTH:
                raise InvalidPasswordError(
                    f"Password must be at least {self._MIN_PASSWORD_LENGTH} characters."
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
            ValueError: If the email is malformed.
            UserNotFoundError: If no user exists with the given email.
            InvalidPasswordError: If the password does not match the stored hash.
        """
        _validate_email(email)

        with _timed_operation("verify_user"):
            user = self._repo.get_by_email(email)
            if not user:
                logger.info(
                    "User login failed: email not found", extra={"email": email}
                )
                raise UserNotFoundError(f"No user found with email '{email}'.")

            if not self._hasher.verify_password(password, user.password_hash):
                logger.info(
                    "User login failed: invalid password", extra={"email": email}
                )
                raise InvalidPasswordError("Invalid password.")

            logger.info("User login success", extra={"email": email})
            return True
