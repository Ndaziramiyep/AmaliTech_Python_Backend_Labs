import logging

import pytest
from src.auth.exceptions import InvalidPasswordError, UserAlreadyExistsError
from src.auth.models import User
from src.auth.service import UserService


def test_register_user_success(mocker):
    """Test that a new user is successfully registered with email and id."""
    mock_repo = mocker.Mock()
    mock_hasher = mocker.Mock()

    # Email does not exist yet
    mock_repo.get_by_email.return_value = None
    # Return fake password hash
    mock_hasher.hash_password.return_value = "hashed_password"

    service = UserService(user_repository=mock_repo, password_hasher=mock_hasher)
    user = service.register_user("Diane", "diane@example.com", "SecurePass123")

    assert isinstance(user, User)
    assert user.username == "Diane"
    assert user.email == "diane@example.com"
    assert user.password_hash == "hashed_password"
    assert user.id is not None  # ID automatically generated

    mock_repo.add.assert_called_once_with(user)
    mock_hasher.hash_password.assert_called_once_with("SecurePass123")


def test_register_user_duplicate(mocker):
    """Test that registering a user with an existing email raises an exception."""
    mock_repo = mocker.Mock()
    mock_hasher = mocker.Mock()

    # Email already exists
    mock_repo.get_by_email.return_value = User(
        username="Diane", email="diane@example.com", password_hash="hashed_password"
    )

    service = UserService(user_repository=mock_repo, password_hasher=mock_hasher)

    with pytest.raises(UserAlreadyExistsError):
        service.register_user("Diane", "diane@example.com", "SecurePass123")


def test_register_user_password_too_short(mocker):
    """Test that registration fails if password is too short."""
    mock_repo = mocker.Mock()
    mock_hasher = mocker.Mock()
    mock_repo.get_by_email.return_value = None

    service = UserService(user_repository=mock_repo, password_hasher=mock_hasher)

    with pytest.raises(InvalidPasswordError):
        service.register_user(
            "Diane", "diane@example.com", "short"
        )  # password < 8 chars


def test_register_calls_repository_add_once(mocker):
    """Ensure the repository's add() method is called exactly once."""
    mock_repo = mocker.Mock()
    mock_hasher = mocker.Mock()
    mock_repo.get_by_email.return_value = None
    mock_hasher.hash_password.return_value = "hashed_password"

    service = UserService(user_repository=mock_repo, password_hasher=mock_hasher)
    service.register_user("Diane", "diane@example.com", "SecurePass123")

    mock_repo.add.assert_called_once()


def test_register_logs_event(mocker, caplog):
    """Test that user registration logs an event."""
    mock_repo = mocker.Mock()
    mock_hasher = mocker.Mock()
    mock_repo.get_by_email.return_value = None
    mock_hasher.hash_password.return_value = "hashed_password"

    service = UserService(user_repository=mock_repo, password_hasher=mock_hasher)

    with caplog.at_level(logging.INFO):
        service.register_user("Diane", "diane@example.com", "SecurePass123")
        assert any("User registered" in record.message for record in caplog.records)
