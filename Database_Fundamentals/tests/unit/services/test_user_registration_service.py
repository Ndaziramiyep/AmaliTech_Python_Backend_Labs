"""Unit tests for UserRegistrationService."""

from __future__ import annotations

from datetime import datetime

from social_platform.models.entities import User
from social_platform.repositories.interfaces import UserRepositoryInterface
from social_platform.services.user_registration_service import UserRegistrationService


class _RecordingUserRepository(UserRepositoryInterface):
    """A stand-in for UserRepositoryInterface that records the arguments it was called with."""

    def __init__(self) -> None:
        self.create_user_calls: list[tuple[str, str, str, str]] = []

    def create_user(self, username: str, email: str, password_hash: str, display_name: str) -> User:
        self.create_user_calls.append((username, email, password_hash, display_name))
        return User(1, username, email, display_name, datetime.now())

    def find_user_by_id(self, user_id: int) -> User | None:
        raise NotImplementedError

    def find_user_and_password_hash_by_username(self, username: str) -> tuple[User, str] | None:
        raise NotImplementedError


def test_register_user_never_passes_the_plaintext_password_to_the_repository() -> None:
    """The repository only ever receives a salted hash, never the plaintext password."""
    user_repository = _RecordingUserRepository()
    service = UserRegistrationService(user_repository)

    service.register_user("ada", "ada@example.com", "Super-secret1", "Ada Lovelace")

    _, _, password_hash, _ = user_repository.create_user_calls[0]
    assert "Super-secret1" not in password_hash
    assert ":" in password_hash


def test_register_user_hashes_the_same_password_differently_each_time() -> None:
    """Each registration uses a fresh random salt, so identical passwords hash differently."""
    user_repository = _RecordingUserRepository()
    service = UserRegistrationService(user_repository)

    service.register_user("ada", "ada@example.com", "Super-secret1", "Ada Lovelace")
    service.register_user("grace", "grace@example.com", "Super-secret1", "Grace Hopper")

    first_hash = user_repository.create_user_calls[0][2]
    second_hash = user_repository.create_user_calls[1][2]
    assert first_hash != second_hash
