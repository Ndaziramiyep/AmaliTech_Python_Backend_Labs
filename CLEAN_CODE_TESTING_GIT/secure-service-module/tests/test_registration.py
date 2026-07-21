"""Tests for user registration logic."""

import logging

import pytest

from src.auth.exceptions import InvalidPasswordError, UserAlreadyExistsError
from src.auth.models import User
from src.auth.service import UserService


def test_register_user_success(mocker):
    """Test that a new user is successfully registered with email and id."""
    mock_repo = mocker.Mock()
    mock_hasher = mocker.Mock()
    mock_repo.get_by_email.return_value = None
    mock_hasher.hash_password.return_value = "hashed_password"

    service = UserService(user_repository=mock_repo, password_hasher=mock_hasher)
    user = service.register_user("Patrick", "patrick@example.com", "Patrick")

    assert isinstance(user, User)
    assert user.username == "Patrick"
    assert user.email == "patrick@example.com"
    assert user.password_hash == "hashed_password"
    assert user.id is not None

    mock_repo.add.assert_called_once_with(user)
    mock_hasher.hash_password.assert_called_once_with("Patrick")


def test_register_user_duplicate(mocker):
    """Test that duplicate email registration raises UserAlreadyExistsError."""
    mock_repo = mocker.Mock()
    mock_hasher = mocker.Mock()
    mock_repo.get_by_email.return_value = User(
        username="Patrick",
        email="patrick@example.com",
        password_hash="hashed_password",
    )

    service = UserService(user_repository=mock_repo, password_hasher=mock_hasher)

    with pytest.raises(UserAlreadyExistsError):
        service.register_user("Patrick", "patrick@example.com", "Patrick")


def test_register_user_password_too_short(mocker):
    """Test that registration fails if password is shorter than 7 characters."""
    mock_repo = mocker.Mock()
    mock_hasher = mocker.Mock()
    mock_repo.get_by_email.return_value = None

    service = UserService(user_repository=mock_repo, password_hasher=mock_hasher)

    with pytest.raises(InvalidPasswordError):
        service.register_user("Patrick", "patrick@example.com", "abc")  # 3 chars


def test_register_calls_repository_add_once(mocker):
    """Ensure the repository's add() method is called exactly once on success."""
    mock_repo = mocker.Mock()
    mock_hasher = mocker.Mock()
    mock_repo.get_by_email.return_value = None
    mock_hasher.hash_password.return_value = "hashed_password"

    service = UserService(user_repository=mock_repo, password_hasher=mock_hasher)
    service.register_user("Patrick", "patrick@example.com", "Patrick")

    mock_repo.add.assert_called_once()


def test_register_logs_event(mocker, caplog):
    """Test that user registration emits an INFO log event."""
    mock_repo = mocker.Mock()
    mock_hasher = mocker.Mock()
    mock_repo.get_by_email.return_value = None
    mock_hasher.hash_password.return_value = "hashed_password"

    service = UserService(user_repository=mock_repo, password_hasher=mock_hasher)

    with caplog.at_level(logging.INFO):
        service.register_user("Patrick", "patrick@example.com", "Patrick")
        assert any("User registered" in record.message for record in caplog.records)
