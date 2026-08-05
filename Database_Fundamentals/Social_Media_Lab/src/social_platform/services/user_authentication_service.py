"""The login use case."""

from __future__ import annotations

from social_platform.models.entities import User
from social_platform.models.exceptions import InvalidCredentialsError
from social_platform.repositories.interfaces import UserRepositoryInterface
from social_platform.security.password_hashing import verify_password


class UserAuthenticationService:
    """Orchestrates verifying a username/password pair against the stored hash."""

    def __init__(self, user_repository: UserRepositoryInterface) -> None:
        self._user_repository = user_repository

    def login(self, username: str, plaintext_password: str) -> User:
        """Return the matching user, or raise `InvalidCredentialsError` if it doesn't match."""
        lookup_result = self._user_repository.find_user_and_password_hash_by_username(username)
        if lookup_result is None:
            raise InvalidCredentialsError("Invalid username or password.")

        user, password_hash = lookup_result
        if not verify_password(plaintext_password, password_hash):
            raise InvalidCredentialsError("Invalid username or password.")
        return user
