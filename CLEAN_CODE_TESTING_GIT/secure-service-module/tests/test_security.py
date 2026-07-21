from unittest.mock import Mock

import pytest
from src.auth.exceptions import InvalidPasswordError, UserNotFoundError
from src.auth.models import User
from src.auth.service import UserService


def test_password_is_hashed_on_registration():
    repo = Mock()
    hasher = Mock()

    repo.get_by_email.return_value = None
    hasher.hash_password.return_value = "hashed-password"

    service = UserService(repo, hasher)

    user = service.register_user(
        username="Diane",
        email="diane@example.com",
        password="PlainPassword123",
    )

    # Hashing must happen
    hasher.hash_password.assert_called_once_with("PlainPassword123")

    # Plain password must NOT be stored
    assert user.password_hash != "PlainPassword123"
    assert user.password_hash == "hashed-password"

    # Repository must store hashed password
    repo.add.assert_called_once()
    stored_user = repo.add.call_args[0][0]
    assert stored_user.password_hash == "hashed-password"


def test_login_verifies_hashed_password():
    repo = Mock()
    hasher = Mock()

    user = User(
        username="Diane",
        email="diane@example.com",
        password_hash="hashed-password",
    )

    repo.get_by_email.return_value = user
    hasher.verify_password.return_value = True

    service = UserService(repo, hasher)

    result = service.verify_user(
        email="diane@example.com",
        password="PlainPassword123",
    )

    hasher.verify_password.assert_called_once_with(
        "PlainPassword123", "hashed-password"
    )

    assert result is True


def test_login_fails_if_password_is_wrong():
    repo = Mock()
    hasher = Mock()

    user = User(
        username="Diane",
        email="diane@example.com",
        password_hash="hashed-password",
    )

    repo.get_by_email.return_value = user
    hasher.verify_password.return_value = False

    service = UserService(repo, hasher)

    with pytest.raises(InvalidPasswordError):
        service.verify_user("diane@example.com", "WrongPassword")


def test_login_fails_if_user_not_found():
    repo = Mock()
    hasher = Mock()

    repo.get_by_email.return_value = None

    service = UserService(repo, hasher)

    with pytest.raises(UserNotFoundError):
        service.verify_user("missing@example.com", "AnyPassword")
