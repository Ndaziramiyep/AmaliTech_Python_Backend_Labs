"""Unit tests for UserService.login."""

from __future__ import annotations

from datetime import datetime

import pytest

from social_platform.common.exceptions import InvalidCredentialsError
from social_platform.common.security import hash_password
from social_platform.features.users.model import User
from social_platform.features.users.service import UserService
from tests.unit.services._fakes import FakeUserRepository


def _seed_user(user_repository: FakeUserRepository, password: str) -> User:
    user = User(1, "ada", "ada@example.com", datetime.now())
    user_repository.users_by_id[user.user_id] = user
    user_repository.password_hashes_by_username[user.username] = hash_password(password)
    return user


def test_login_returns_the_user_for_correct_credentials(
    fake_user_repository: FakeUserRepository,
) -> None:
    """A username/password pair matching the stored hash returns that user."""
    user = _seed_user(fake_user_repository, "super-secret")
    service = UserService(fake_user_repository)

    assert service.login("ada", "super-secret") == user


def test_login_rejects_an_incorrect_password(fake_user_repository: FakeUserRepository) -> None:
    """A wrong password raises InvalidCredentialsError, not a different exception."""
    _seed_user(fake_user_repository, "super-secret")
    service = UserService(fake_user_repository)

    with pytest.raises(InvalidCredentialsError):
        service.login("ada", "wrong-password")


def test_login_rejects_an_unknown_username(fake_user_repository: FakeUserRepository) -> None:
    """A username with no matching account raises InvalidCredentialsError."""
    service = UserService(fake_user_repository)

    with pytest.raises(InvalidCredentialsError):
        service.login("nobody", "anything")
