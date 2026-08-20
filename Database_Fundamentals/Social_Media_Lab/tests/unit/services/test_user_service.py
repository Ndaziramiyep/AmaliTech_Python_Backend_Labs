import pytest

from social.services.user_service import UserService

from .fakes import FakeActivityLogger, FakeUnitOfWork, FakeUserRepository


class DuplicateUsernameViolation(Exception):
    """Stand-in for the users.username UNIQUE violation."""


def test_register_commits_once_then_logs_activity():
    repository = FakeUserRepository()
    uow = FakeUnitOfWork()
    logger = FakeActivityLogger()
    service = UserService(lambda: uow, repository, logger)

    result = service.register(username="ada", email="ada@example.com")

    assert result.id == 1
    assert result.username == "ada"
    assert result.email == "ada@example.com"
    assert repository.received_cursor is uow.cursor
    assert uow.committed is True
    assert uow.rolled_back is False
    assert logger.entries == [("user_registered", {"user_id": 1, "username": "ada"})]


def test_register_rolls_back_and_leaves_no_side_effects_when_insert_fails():
    error = DuplicateUsernameViolation("users_username_key")
    repository = FakeUserRepository(raise_error=error)
    uow = FakeUnitOfWork()
    logger = FakeActivityLogger()
    service = UserService(lambda: uow, repository, logger)

    with pytest.raises(DuplicateUsernameViolation):
        service.register(username="ada", email="ada@example.com")

    assert uow.committed is False
    assert uow.rolled_back is True
    assert logger.entries == []
