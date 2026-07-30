"""Tests for UserService: registration, login, and input validation."""

import logging

import pytest

from src.auth.exceptions import (
    InvalidPasswordError,
    UserAlreadyExistsError,
    UserNotFoundError,
    WeakPasswordError,
)
from src.auth.models import User
from src.auth.service import UserService

_EXISTING_USER = User(
    username="Patrick", email="patrick@gmail.com", password_hash="hashed_password"
)


def _make_service(
    mocker, existing_user=None, hashed="hashed_password", password_matches=True
):
    mock_repo = mocker.Mock()
    mock_hasher = mocker.Mock()
    mock_repo.get_user_by_email.return_value = existing_user
    mock_hasher.hash_password.return_value = hashed
    if not password_matches:
        mock_hasher.verify_password.side_effect = InvalidPasswordError(
            "Invalid password."
        )
    return UserService(user_repository=mock_repo, password_hasher=mock_hasher), (
        mock_repo,
        mock_hasher,
    )


@pytest.fixture
def service(mocker):
    """A UserService backed by mocks, with no existing users."""
    return _make_service(mocker)[0]


# --- registration ---------------------------------------------------------


def test_register_user_success(mocker):
    """A new user is registered with a hashed password and generated id."""
    service, (mock_repo, mock_hasher) = _make_service(mocker)

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
    service, _ = _make_service(mocker, existing_user=_EXISTING_USER)

    with pytest.raises(UserAlreadyExistsError):
        service.register_user("Patrick", "patrick@gmail.com", "SecurePass1")


@pytest.mark.parametrize(
    "password",
    [
        "Short1!",  # shorter than 8 characters
        "alllowercase1!",  # missing an uppercase letter
        "ALLUPPERCASE1!",  # missing a lowercase letter
        "NoDigitsHere!",  # missing a digit
        "NoSpecialChar1",  # missing a special character
    ],
)
def test_register_rejects_weak_passwords(mocker, password):
    """A password failing the strength policy raises WeakPasswordError."""
    service, _ = _make_service(mocker)

    with pytest.raises(WeakPasswordError):
        service.register_user("Patrick", "patrick@gmail.com", password)


def test_register_calls_repository_add_exactly_once(mocker):
    """A successful registration persists the user exactly once."""
    service, (mock_repo, _) = _make_service(mocker)

    service.register_user("Patrick", "patrick@gmail.com", "SecurePass1!")

    mock_repo.add_user.assert_called_once()


def test_register_logs_success_event(mocker, caplog):
    """A successful registration emits an INFO-level structured log event."""
    service, _ = _make_service(mocker)

    with caplog.at_level(logging.INFO):
        service.register_user("Patrick", "patrick@gmail.com", "SecurePass1!")

    assert any("User registered" in record.message for record in caplog.records)


# --- login ------------------------------------------------------------------


def test_verify_user_success(mocker):
    """Correct credentials for an existing user verify successfully."""
    service, (_, mock_hasher) = _make_service(mocker, existing_user=_EXISTING_USER)

    result = service.verify_user("patrick@gmail.com", "SecurePass1")

    assert result is True
    mock_hasher.verify_password.assert_called_once_with(
        "SecurePass1", "hashed_password"
    )


def test_verify_user_raises_when_email_not_found(mocker):
    """Verifying an email with no matching user raises UserNotFoundError."""
    service, _ = _make_service(mocker, existing_user=None)

    with pytest.raises(UserNotFoundError):
        service.verify_user("unknown@gmail.com", "AnyPassword1")


def test_verify_user_raises_on_wrong_password(mocker):
    """Verifying with a wrong password raises InvalidPasswordError."""
    service, _ = _make_service(
        mocker, existing_user=_EXISTING_USER, password_matches=False
    )

    with pytest.raises(InvalidPasswordError):
        service.verify_user("patrick@gmail.com", "WrongPassword1")


def test_verify_user_logs_success_event(mocker, caplog):
    """A successful login emits an INFO-level structured log event."""
    service, _ = _make_service(mocker, existing_user=_EXISTING_USER)

    with caplog.at_level(logging.INFO):
        service.verify_user("patrick@gmail.com", "SecurePass1")

    assert any("User login success" in record.message for record in caplog.records)


def test_verify_user_logs_failure_event_on_missing_user(mocker, caplog):
    """A login attempt for a missing user emits an INFO-level failure log."""
    service, _ = _make_service(mocker, existing_user=None)

    with caplog.at_level(logging.INFO):
        with pytest.raises(UserNotFoundError):
            service.verify_user("unknown@gmail.com", "AnyPassword1")

    assert any("User login failed" in record.message for record in caplog.records)


def test_verify_user_logs_failure_event_on_wrong_password(mocker, caplog):
    """A login attempt with a wrong password emits an INFO-level failure log."""
    service, _ = _make_service(
        mocker, existing_user=_EXISTING_USER, password_matches=False
    )

    with caplog.at_level(logging.INFO):
        with pytest.raises(InvalidPasswordError):
            service.verify_user("patrick@gmail.com", "WrongPassword1")

    assert any("User login failed" in record.message for record in caplog.records)


# --- validation --------------------------------------------------------------


@pytest.mark.parametrize("username", ["", "   ", "\t\n"])
def test_register_rejects_empty_or_blank_username(service, username):
    """An empty or whitespace-only username is rejected before any lookup."""
    with pytest.raises(ValueError, match="Username"):
        service.register_user(username, "patrick@gmail.com", "SecurePass1")


@pytest.mark.parametrize(
    "email",
    ["", "not-an-email", "missing-domain@", "@missing-local.com", "no-at-sign.com"],
)
def test_register_rejects_malformed_email(service, email):
    """A malformed email is rejected before any repository lookup."""
    with pytest.raises(ValueError, match="valid email"):
        service.register_user("Patrick", email, "SecurePass1")


def test_register_accepts_well_formed_email(service):
    """A normal, well-formed email passes validation and registration succeeds."""
    user = service.register_user("Patrick", "patrick@gmail.com", "SecurePass1!")
    assert user.email == "patrick@gmail.com"


@pytest.mark.parametrize(
    "email", ["", "not-an-email", "missing-domain@", "@missing-local.com"]
)
def test_verify_rejects_malformed_email(service, email):
    """Login also rejects malformed emails before touching the repository."""
    with pytest.raises(ValueError, match="valid email"):
        service.verify_user(email, "SecurePass1")
