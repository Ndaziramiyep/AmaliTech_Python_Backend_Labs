"""Tests for login / credential verification logic."""

import logging

import pytest

from src.auth.exceptions import InvalidPasswordError, UserNotFoundError
from src.auth.models import User
from src.auth.service import UserService

_EXISTING_USER = User(
    username="Patrick", email="patrick@gmail.com", password_hash="hashed_password"
)


def _service(mocker, existing_user=_EXISTING_USER, password_matches=True):
    mock_repo = mocker.Mock()
    mock_hasher = mocker.Mock()
    mock_repo.get_by_email.return_value = existing_user
    mock_hasher.verify_password.return_value = password_matches
    return UserService(user_repository=mock_repo, password_hasher=mock_hasher), (
        mock_repo,
        mock_hasher,
    )


def test_verify_user_success(mocker):
    """Correct credentials for an existing user verify successfully."""
    service, (_, mock_hasher) = _service(mocker)

    result = service.verify_user("patrick@gmail.com", "SecurePass1")

    assert result is True
    mock_hasher.verify_password.assert_called_once_with(
        "SecurePass1", "hashed_password"
    )


def test_verify_user_raises_when_email_not_found(mocker):
    """Verifying an email with no matching user raises UserNotFoundError."""
    service, _ = _service(mocker, existing_user=None)

    with pytest.raises(UserNotFoundError):
        service.verify_user("unknown@gmail.com", "AnyPassword1")


def test_verify_user_raises_on_wrong_password(mocker):
    """Verifying with a wrong password raises InvalidPasswordError."""
    service, _ = _service(mocker, password_matches=False)

    with pytest.raises(InvalidPasswordError):
        service.verify_user("patrick@gmail.com", "WrongPassword1")


def test_verify_user_logs_success_event(mocker, caplog):
    """A successful login emits an INFO-level structured log event."""
    service, _ = _service(mocker)

    with caplog.at_level(logging.INFO):
        service.verify_user("patrick@gmail.com", "SecurePass1")

    assert any("User login success" in record.message for record in caplog.records)


def test_verify_user_logs_failure_event_on_missing_user(mocker, caplog):
    """A login attempt for a missing user emits an INFO-level failure log."""
    service, _ = _service(mocker, existing_user=None)

    with caplog.at_level(logging.INFO):
        with pytest.raises(UserNotFoundError):
            service.verify_user("unknown@gmail.com", "AnyPassword1")

    assert any("User login failed" in record.message for record in caplog.records)


def test_verify_user_logs_failure_event_on_wrong_password(mocker, caplog):
    """A login attempt with a wrong password emits an INFO-level failure log."""
    service, _ = _service(mocker, password_matches=False)

    with caplog.at_level(logging.INFO):
        with pytest.raises(InvalidPasswordError):
            service.verify_user("patrick@gmail.com", "WrongPassword1")

    assert any("User login failed" in record.message for record in caplog.records)
