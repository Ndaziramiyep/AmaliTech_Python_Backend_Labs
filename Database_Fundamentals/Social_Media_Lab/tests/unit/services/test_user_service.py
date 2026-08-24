"""Unit tests for UserService against fake repository, unit-of-work, and activity-logger collaborators."""
import pytest

from social.services.user_service import UserService

from .fakes import FakeActivityLogger, FakeUnitOfWork, FakeUserRepository


class DuplicateUsernameViolation(Exception):
    """Stand-in for the users.username UNIQUE violation."""


def test_register_commits_once_then_logs_activity():
    """Test that registering a user commits exactly once and then logs a user_registered activity event."""
    repository = FakeUserRepository()
    uow = FakeUnitOfWork()
    logger = FakeActivityLogger()
    service = UserService(lambda: uow, repository, logger)

    result = service.register(username="ada", email="ada@example.com", password="secret123")

    assert result.id == 1
    assert result.username == "ada"
    assert result.email == "ada@example.com"
    assert result.password_hash != "secret123"
    assert repository.received_cursor is uow.cursor
    assert uow.committed is True
    assert uow.rolled_back is False
    assert logger.entries == [("user_registered", {"user_id": 1, "username": "ada"})]


def test_register_rolls_back_and_leaves_no_side_effects_when_insert_fails():
    """Test that a failed user insert rolls back the transaction and logs no activity."""
    error = DuplicateUsernameViolation("users_username_key")
    repository = FakeUserRepository(raise_error=error)
    uow = FakeUnitOfWork()
    logger = FakeActivityLogger()
    service = UserService(lambda: uow, repository, logger)

    with pytest.raises(DuplicateUsernameViolation):
        service.register(username="ada", email="ada@example.com", password="secret123")

    assert uow.committed is False
    assert uow.rolled_back is True
    assert logger.entries == []


def test_authenticate_returns_the_user_when_the_password_matches():
    """Test that authenticate returns the user when the given password matches."""
    repository = FakeUserRepository()
    uow = FakeUnitOfWork()
    logger = FakeActivityLogger()
    service = UserService(lambda: uow, repository, logger)
    service.register(username="ada", email="ada@example.com", password="secret123")

    result = service.authenticate("ada@example.com", "secret123")

    assert result is not None
    assert result.username == "ada"


def test_authenticate_returns_none_when_the_password_is_wrong():
    """Test that authenticate returns None when the given password is wrong."""
    repository = FakeUserRepository()
    uow = FakeUnitOfWork()
    logger = FakeActivityLogger()
    service = UserService(lambda: uow, repository, logger)
    service.register(username="ada", email="ada@example.com", password="secret123")

    assert service.authenticate("ada@example.com", "wrong-password") is None


def test_authenticate_returns_none_when_no_user_has_that_email():
    """Test that authenticate returns None when no user has the given email."""
    repository = FakeUserRepository()
    uow = FakeUnitOfWork()
    logger = FakeActivityLogger()
    service = UserService(lambda: uow, repository, logger)

    assert service.authenticate("nobody@example.com", "whatever") is None


def test_find_by_username_returns_the_matching_registered_user():
    """Test that find_by_username returns the registered user matching that username."""
    repository = FakeUserRepository()
    uow = FakeUnitOfWork()
    logger = FakeActivityLogger()
    service = UserService(lambda: uow, repository, logger)
    service.register(username="ada", email="ada@example.com", password="secret123")

    result = service.find_by_username("ada")

    assert result is not None
    assert result.username == "ada"


def test_find_by_username_returns_none_when_no_such_user():
    """Test that find_by_username returns None when no user has that username."""
    repository = FakeUserRepository()
    uow = FakeUnitOfWork()
    logger = FakeActivityLogger()
    service = UserService(lambda: uow, repository, logger)

    assert service.find_by_username("nobody") is None


def test_list_users_returns_every_registered_user_in_order():
    """Test that list_users returns every registered user in registration order."""
    repository = FakeUserRepository()
    uow = FakeUnitOfWork()
    logger = FakeActivityLogger()
    service = UserService(lambda: uow, repository, logger)
    service.register(username="ada", email="ada@example.com", password="secret123")
    service.register(username="bob", email="bob@example.com", password="secret456")

    result = service.list_users()

    assert [u.username for u in result] == ["ada", "bob"]
