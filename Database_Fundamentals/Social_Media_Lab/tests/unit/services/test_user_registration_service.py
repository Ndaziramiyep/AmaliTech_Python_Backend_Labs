"""Unit tests for UserService.register."""

from __future__ import annotations

from datetime import datetime

import pytest

from social_platform.common.exceptions import (
    InvalidEmailError,
    InvalidUsernameError,
    WeakPasswordError,
)
from social_platform.features.users.model import User
from social_platform.features.users.service import UserService


class _RecordingUserRepository:
    """A stand-in for UserRepository that records the arguments it was called with."""

    def __init__(self) -> None:
        self.create_user_calls: list[tuple[str, str, str]] = []

    def create_user(self, username: str, email: str, password_hash: str) -> User:
        self.create_user_calls.append((username, email, password_hash))
        return User(1, username, email, datetime.now())

    def find_user_and_password_hash_by_username(self, username: str) -> tuple[User, str] | None:
        raise NotImplementedError


def test_register_never_passes_the_plaintext_password_to_the_repository() -> None:
    """The repository only ever receives a salted hash, never the plaintext password."""
    user_repository = _RecordingUserRepository()
    service = UserService(user_repository)

    service.register("ada", "ada@example.com", "Super-secret1")

    _, _, password_hash = user_repository.create_user_calls[0]
    assert "Super-secret1" not in password_hash
    assert ":" in password_hash


def test_register_hashes_the_same_password_differently_each_time() -> None:
    """Each registration uses a fresh random salt, so identical passwords hash differently."""
    user_repository = _RecordingUserRepository()
    service = UserService(user_repository)

    service.register("ada", "ada@example.com", "Super-secret1")
    service.register("grace", "grace@example.com", "Super-secret1")

    first_hash = user_repository.create_user_calls[0][2]
    second_hash = user_repository.create_user_calls[1][2]
    assert first_hash != second_hash


def test_register_rejects_an_invalid_username_before_touching_the_repository() -> None:
    """A malformed username is rejected without ever reaching the repository."""
    user_repository = _RecordingUserRepository()
    service = UserService(user_repository)

    with pytest.raises(InvalidUsernameError):
        service.register("a", "ada@example.com", "Super-secret1")

    assert user_repository.create_user_calls == []


def test_register_rejects_an_invalid_email_before_touching_the_repository() -> None:
    """A malformed email is rejected without ever reaching the repository."""
    user_repository = _RecordingUserRepository()
    service = UserService(user_repository)

    with pytest.raises(InvalidEmailError):
        service.register("ada", "not-an-email", "Super-secret1")

    assert user_repository.create_user_calls == []


def test_register_rejects_a_weak_password_before_touching_the_repository() -> None:
    """A password failing the strength policy is rejected without hashing or persisting it."""
    user_repository = _RecordingUserRepository()
    service = UserService(user_repository)

    with pytest.raises(WeakPasswordError):
        service.register("ada", "ada@example.com", "weak")

    assert user_repository.create_user_calls == []
