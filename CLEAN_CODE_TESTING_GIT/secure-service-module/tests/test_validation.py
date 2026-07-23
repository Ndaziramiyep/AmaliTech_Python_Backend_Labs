"""Tests for input validation on username and email during registration/login."""

import pytest

from src.auth.service import UserService


@pytest.fixture
def service(mocker):
    """A UserService backed by mocks, with no existing users."""
    mock_repo = mocker.Mock()
    mock_hasher = mocker.Mock()
    mock_repo.get_by_email.return_value = None
    mock_hasher.hash_password.return_value = "hashed_password"
    return UserService(user_repository=mock_repo, password_hasher=mock_hasher)


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
    user = service.register_user("Patrick", "patrick@gmail.com", "SecurePass1")
    assert user.email == "patrick@gmail.com"


@pytest.mark.parametrize(
    "email", ["", "not-an-email", "missing-domain@", "@missing-local.com"]
)
def test_verify_rejects_malformed_email(service, email):
    """Login also rejects malformed emails before touching the repository."""
    with pytest.raises(ValueError, match="valid email"):
        service.verify_user(email, "SecurePass1")
