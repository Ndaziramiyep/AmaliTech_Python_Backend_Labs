"""User account use cases: registration, login, bio management, and search."""

from __future__ import annotations

import logging
from datetime import UTC, datetime

from social_platform.common.exceptions import InvalidCredentialsError
from social_platform.common.security import (
    hash_password,
    validate_password_strength,
    verify_password,
)
from social_platform.common.validation import validate_bio, validate_email, validate_username
from social_platform.features.activity_log.model import ActivityEvent, ActivityEventType
from social_platform.features.activity_log.repository import ActivityLogRepository
from social_platform.features.users.model import User
from social_platform.features.users.repository import UserRepository

_logger = logging.getLogger(__name__)
_DEFAULT_SEARCH_LIMIT = 10


class UserService:
    """Orchestrates registering, logging in, and managing a user's own bio."""

    def __init__(
        self, user_repository: UserRepository, activity_log_repository: ActivityLogRepository
    ) -> None:
        self._user_repository = user_repository
        self._activity_log_repository = activity_log_repository

    def register(
        self, username: str, email: str, plaintext_password: str, bio: str | None = None
    ) -> User:
        """Register a new user; the plaintext password is never persisted, only its hash."""
        validate_username(username)
        validate_email(email)
        validate_password_strength(plaintext_password)
        if bio:
            validate_bio(bio)

        password_hash = hash_password(plaintext_password)
        return self._user_repository.create_user(username, email, password_hash, bio or None)

    def login(self, username: str, plaintext_password: str) -> User:
        """Return the matching user, or raise `InvalidCredentialsError` if it doesn't match."""
        lookup_result = self._user_repository.find_user_and_password_hash_by_username(username)
        if lookup_result is None:
            raise InvalidCredentialsError("Invalid username or password.")

        user, password_hash = lookup_result
        if not verify_password(plaintext_password, password_hash):
            raise InvalidCredentialsError("Invalid username or password.")
        return user

    def update_bio(self, user_id: int, bio: str | None) -> User:
        """Replace a user's bio; an empty or missing bio simply clears it."""
        if bio:
            validate_bio(bio)
        user = self._user_repository.update_bio(user_id, bio or None)
        try:
            self._activity_log_repository.record_activity_event(
                ActivityEvent(
                    event_type=ActivityEventType.BIO_UPDATED,
                    actor_user_id=user_id,
                    occurred_at=datetime.now(UTC),
                )
            )
        except Exception:
            _logger.exception("Failed to record bio_updated activity event for user %s.", user_id)
        return user

    def search_users(self, query: str, result_limit: int = _DEFAULT_SEARCH_LIMIT) -> list[User]:
        """Return users whose username contains `query`, alphabetically."""
        return self._user_repository.search_users_by_username(query, result_limit)
