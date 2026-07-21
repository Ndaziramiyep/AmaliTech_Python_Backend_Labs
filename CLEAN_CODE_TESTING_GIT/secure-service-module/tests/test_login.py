import logging

import pytest
from src.auth.exceptions import InvalidPasswordError, UserNotFoundError
from src.auth.models import User
from src.auth.service import UserService


def test_login_success(mocker):
    """Test successful login with correct email and password."""
    mock_repo = mocker.Mock()
    mock_hasher = mocker.Mock()

    # User exists
    user = User(
        username="Diane", email="diane@example.com", password_hash="hashed_password"
    )
    mock_repo.get_by_email.return_value = user
    mock_hasher.verify_password.return_value = True

    service = UserService(user_repository=mock_repo, password_hasher=mock_hasher)
    result = service.verify_user("diane@example.com", "SecurePass123")

    assert result is True
    mock_hasher.verify_password.assert_called_once_with(
        "SecurePass123", "hashed_password"
    )


def test_login_nonexistent_email(mocker):
    """Test that login with an email that doesn't exist raises UserNotFoundError."""
    mock_repo = mocker.Mock()
    mock_hasher = mocker.Mock()
    mock_repo.get_by_email.return_value = None

    service = UserService(user_repository=mock_repo, password_hasher=mock_hasher)

    with pytest.raises(UserNotFoundError):
        service.verify_user("unknown@example.com", "AnyPassword")


def test_login_invalid_password(mocker):
    """Test that login with wrong password raises InvalidPasswordError."""
    mock_repo = mocker.Mock()
    mock_hasher = mocker.Mock()

    # User exists
    user = User(
        username="Diane", email="diane@example.com", password_hash="hashed_password"
    )
    mock_repo.get_by_email.return_value = user
    mock_hasher.verify_password.return_value = False

    service = UserService(user_repository=mock_repo, password_hasher=mock_hasher)

    with pytest.raises(InvalidPasswordError):
        service.verify_user("diane@example.com", "WrongPassword")


def test_login_logs_event_success(mocker, caplog):
    """Test that successful login logs an event."""
    mock_repo = mocker.Mock()
    mock_hasher = mocker.Mock()
    user = User(
        username="Diane", email="diane@example.com", password_hash="hashed_password"
    )
    mock_repo.get_by_email.return_value = user
    mock_hasher.verify_password.return_value = True

    service = UserService(user_repository=mock_repo, password_hasher=mock_hasher)

    with caplog.at_level(logging.INFO):
        service.verify_user("diane@example.com", "SecurePass123")
        assert any("User login success" in record.message for record in caplog.records)


def test_login_logs_event_failure(mocker, caplog):
    """Test that failed login logs an event."""
    mock_repo = mocker.Mock()
    mock_hasher = mocker.Mock()
    user = User(
        username="Diane", email="diane@example.com", password_hash="hashed_password"
    )
    mock_repo.get_by_email.return_value = user
    mock_hasher.verify_password.return_value = False

    service = UserService(user_repository=mock_repo, password_hasher=mock_hasher)

    with caplog.at_level(logging.INFO):
        with pytest.raises(InvalidPasswordError):
            service.verify_user("diane@example.com", "WrongPassword")
        assert any("User login failed" in record.message for record in caplog.records)
