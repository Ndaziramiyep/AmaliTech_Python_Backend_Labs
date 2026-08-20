"""Unit tests for UserService.register."""

from __future__ import annotations

from datetime import datetime

import pytest

from social_platform.common.exceptions import (
    InvalidBioError,
    InvalidEmailError,
    InvalidUsernameError,
    WeakPasswordError,
)
from social_platform.features.users.model import User
from social_platform.features.users.service import UserService
from tests.unit.services._fakes import FakeActivityLogRepository


class _RecordingUserRepository:
    """A stand-in for UserRepository that records the arguments it was called with."""

    def __init__(self) -> None:
        self.create_user_calls: list[tuple[str, str, str, str | None]] = []

    def create_user(
        self, username: str, email: str, password_hash: str, bio: str | None = None
    ) -> User:
        self.create_user_calls.append((username, email, password_hash, bio))
        return User(1, username, email, bio, datetime.now())

    def find_user_and_password_hash_by_username(self, username: str) -> tuple[User, str] | None:
        raise NotImplementedError

    def find_user_by_username(self, username: str) -> User | None:
        raise NotImplementedError

    def update_bio(self, user_id: int, bio: str | None) -> User:
        raise NotImplementedError

    def search_users_by_username(self, query: str, result_limit: int) -> list[User]:
        raise NotImplementedError


def _build_service(user_repository: _RecordingUserRepository) -> UserService:
    return UserService(user_repository, FakeActivityLogRepository())


def test_register_never_passes_the_plaintext_password_to_the_repository() -> None:
    """The repository only ever receives a salted hash, never the plaintext password."""
    user_repository = _RecordingUserRepository()
    service = _build_service(user_repository)

    service.register("ada", "ada@example.com", "Super-secret1")

    _, _, password_hash, _ = user_repository.create_user_calls[0]
    assert "Super-secret1" not in password_hash
    assert ":" in password_hash


def test_register_hashes_the_same_password_differently_each_time() -> None:
    """Each registration uses a fresh random salt, so identical passwords hash differently."""
    user_repository = _RecordingUserRepository()
    service = _build_service(user_repository)

    service.register("ada", "ada@example.com", "Super-secret1")
    service.register("grace", "grace@example.com", "Super-secret1")

    first_hash = user_repository.create_user_calls[0][2]
    second_hash = user_repository.create_user_calls[1][2]
    assert first_hash != second_hash


def test_register_passes_the_bio_through_unchanged() -> None:
    """A provided bio is forwarded to the repository as-is."""
    user_repository = _RecordingUserRepository()
    service = _build_service(user_repository)

    service.register("ada", "ada@example.com", "Super-secret1", bio="Mathematician.")

    assert user_repository.create_user_calls[0][3] == "Mathematician."


def test_register_with_no_bio_passes_none() -> None:
    """Registering without a bio stores None, not an empty string."""
    user_repository = _RecordingUserRepository()
    service = _build_service(user_repository)

    service.register("ada", "ada@example.com", "Super-secret1")

    assert user_repository.create_user_calls[0][3] is None


def test_register_rejects_a_bio_that_is_too_long() -> None:
    """A bio over the length limit is rejected without ever reaching the repository."""
    user_repository = _RecordingUserRepository()
    service = _build_service(user_repository)

    with pytest.raises(InvalidBioError):
        service.register("ada", "ada@example.com", "Super-secret1", bio="x" * 281)

    assert user_repository.create_user_calls == []


def test_register_rejects_an_invalid_username_before_touching_the_repository() -> None:
    """A malformed username is rejected without ever reaching the repository."""
    user_repository = _RecordingUserRepository()
    service = _build_service(user_repository)

    with pytest.raises(InvalidUsernameError):
        service.register("a", "ada@example.com", "Super-secret1")

    assert user_repository.create_user_calls == []


def test_register_rejects_an_invalid_email_before_touching_the_repository() -> None:
    """A malformed email is rejected without ever reaching the repository."""
    user_repository = _RecordingUserRepository()
    service = _build_service(user_repository)

    with pytest.raises(InvalidEmailError):
        service.register("ada", "not-an-email", "Super-secret1")

    assert user_repository.create_user_calls == []


def test_register_rejects_a_weak_password_before_touching_the_repository() -> None:
    """A password failing the strength policy is rejected without hashing or persisting it."""
    user_repository = _RecordingUserRepository()
    service = _build_service(user_repository)

    with pytest.raises(WeakPasswordError):
        service.register("ada", "ada@example.com", "weak")

    assert user_repository.create_user_calls == []
