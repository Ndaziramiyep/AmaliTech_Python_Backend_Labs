"""Tests for user registration logic."""

import logging

import pytest

from src.auth.exceptions import UserAlreadyExistsError, WeakPasswordError
from src.auth.models import User
from src.auth.service import UserService


def _service(mocker, existing_user=None, hashed="hashed_password"):
    mock_repo = mocker.Mock()
    mock_hasher = mocker.Mock()
    mock_repo.get_user_by_email.return_value = existing_user
    mock_hasher.hash_password.return_value = hashed
    return UserService(user_repository=mock_repo, password_hasher=mock_hasher), (
        mock_repo,
        mock_hasher,
    )


def test_register_user_success(mocker):
    """A new user is registered with a hashed password and generated id."""
    service, (mock_repo, mock_hasher) = _service(mocker)

    user = service.register_user("Patrick", "patrick@gmail.com", "SecurePass1!")

    assert isinstance(user, User)
    assert user.username == "Patrick"
    assert user.email == "patrick@gmail.com"
    assert user.password_hash == "hashed_password"
    assert user.id is not None

    mock_repo.add_user.assert_called_once_with(user)
    mock_hasher.hash_password.assert_called_once_with("SecurePass1!")


def test_register_user_duplicate_email_raises(mocker):
    """Registering with an email that already exists raises UserAlreadyExistsError."""
    existing = User(
        username="Patrick", email="patrick@gmail.com", password_hash="hashed"
    )
    service, _ = _service(mocker, existing_user=existing)

    with pytest.raises(UserAlreadyExistsError):
        service.register_user("Patrick", "patrick@gmail.com", "SecurePass1")


@pytest.mark.parametrize(
    "password",
    [
        "Short1!",          # shorter than 8 characters
        "alllowercase1!",   # missing an uppercase letter
        "ALLUPPERCASE1!",   # missing a lowercase letter
        "NoDigitsHere!",    # missing a digit
        "NoSpecialChar1",   # missing a special character
    ],
)
def test_register_rejects_weak_passwords(mocker, password):
    """A password failing the strength policy raises WeakPasswordError."""
    service, _ = _service(mocker)

    with pytest.raises(WeakPasswordError):
        service.register_user("Patrick", "patrick@gmail.com", password)


def test_register_calls_repository_add_exactly_once(mocker):
    """A successful registration persists the user exactly once."""
    service, (mock_repo, _) = _service(mocker)

    service.register_user("Patrick", "patrick@gmail.com", "SecurePass1!")

    mock_repo.add_user.assert_called_once()


def test_register_logs_success_event(mocker, caplog):
    """A successful registration emits an INFO-level structured log event."""
    service, _ = _service(mocker)

    with caplog.at_level(logging.INFO):
        service.register_user("Patrick", "patrick@gmail.com", "SecurePass1!")

    assert any("User registered" in record.message for record in caplog.records)
