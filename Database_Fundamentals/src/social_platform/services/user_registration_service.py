"""The user-registration use case."""

from __future__ import annotations

from social_platform.models.entities import User
from social_platform.repositories.interfaces import UserRepositoryInterface
from social_platform.security.password_hashing import hash_password
from social_platform.security.password_policy import validate_password_strength
from social_platform.validation import validate_email, validate_username


class UserRegistrationService:
    """Orchestrates registering a new user, salting and hashing their password first."""

    def __init__(self, user_repository: UserRepositoryInterface) -> None:
        self._user_repository = user_repository

    def register_user(
        self, username: str, email: str, plaintext_password: str, display_name: str
    ) -> User:
        """Register a new user; the plaintext password is never persisted, only its hash."""
        validate_username(username)
        validate_email(email)
        validate_password_strength(plaintext_password)

        password_hash = hash_password(plaintext_password)
        return self._user_repository.create_user(username, email, password_hash, display_name)
