"""UserService -- core authentication business logic."""

import logging
import re

from src.auth.exceptions import (
    InvalidPasswordError,
    UserAlreadyExistsError,
    UserNotFoundError,
    WeakPasswordError,
)
from src.auth.interfaces import PasswordHasher, UserRepository
from src.auth.models import User

logger = logging.getLogger(__name__)

_EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_MIN_PASSWORD_LENGTH = 8


def _validate_username(username: str) -> None:
    """Raise ValueError if username is empty or only whitespace."""
    if not username or not username.strip():
        raise ValueError("Username must not be empty.")


def _validate_email(email: str) -> None:
    """Raise ValueError if email is not local-part@domain.tld shaped."""
    if not email or not _EMAIL_PATTERN.match(email):
        raise ValueError(f"'{email}' is not a valid email address.")


def _validate_password_strength(password: str) -> None:
    """Raise WeakPasswordError unless password meets the strength policy."""
    is_strong = (
        len(password) >= _MIN_PASSWORD_LENGTH
        and any(char.isupper() for char in password)
        and any(char.islower() for char in password)
        and any(char.isdigit() for char in password)
        and any(not char.isalnum() for char in password)
    )
    if not is_strong:
        raise WeakPasswordError(
            f"Password must be at least {_MIN_PASSWORD_LENGTH} characters and "
            "include an uppercase letter, a lowercase letter, a digit, and a "
            "special character."
        )


class UserService:
    """Registers and logs in users via injected UserRepository/PasswordHasher."""

    def __init__(
        self, user_repository: UserRepository, password_hasher: PasswordHasher
    ) -> None:
        self._repo = user_repository
        self._hasher = password_hasher

    def register_user(self, username: str, email: str, password: str) -> User:
        """Register a new user with a hashed password."""
        _validate_username(username)
        _validate_email(email)

        if self._repo.get_user_by_email(email):
            raise UserAlreadyExistsError(f"User with email '{email}' already exists.")

        _validate_password_strength(password)

        password_hash = self._hasher.hash_password(password)
        user = User(username=username, email=email, password_hash=password_hash)
        self._repo.add_user(user)
        logger.info("User registered", extra={"email": user.email})
        return user

    def verify_user(self, email: str, password: str) -> bool:
        """Verify a user's credentials, raising on any failure."""
        _validate_email(email)

        user = self._repo.get_user_by_email(email)
        if not user:
            logger.info("User login failed: email not found", extra={"email": email})
            raise UserNotFoundError(f"No user found with email '{email}'.")

        try:
            self._hasher.verify_password(password, user.password_hash)
        except InvalidPasswordError:
            logger.info("User login failed: invalid password", extra={"email": email})
            raise

        logger.info("User login success", extra={"email": email})
        return True
