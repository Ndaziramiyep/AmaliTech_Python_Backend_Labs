"""User account use cases: registration and login."""

from __future__ import annotations

from social_platform.common.exceptions import InvalidCredentialsError
from social_platform.common.security import (
    hash_password,
    validate_password_strength,
    verify_password,
)
from social_platform.common.validation import validate_email, validate_username
from social_platform.features.users.model import User
from social_platform.features.users.repository import UserRepository


class UserService:
    """Orchestrates registering a new user and logging an existing one in."""

    def __init__(self, user_repository: UserRepository) -> None:
        self._user_repository = user_repository

    def register(
        self, username: str, email: str, plaintext_password: str, display_name: str
    ) -> User:
        """Register a new user; the plaintext password is never persisted, only its hash."""
        validate_username(username)
        validate_email(email)
        validate_password_strength(plaintext_password)

        password_hash = hash_password(plaintext_password)
        return self._user_repository.create_user(username, email, password_hash, display_name)

    def login(self, username: str, plaintext_password: str) -> User:
        """Return the matching user, or raise `InvalidCredentialsError` if it doesn't match."""
        lookup_result = self._user_repository.find_user_and_password_hash_by_username(username)
        if lookup_result is None:
            raise InvalidCredentialsError("Invalid username or password.")

        user, password_hash = lookup_result
        if not verify_password(plaintext_password, password_hash):
            raise InvalidCredentialsError("Invalid username or password.")
        return user
