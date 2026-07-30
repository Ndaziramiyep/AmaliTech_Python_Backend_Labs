"""Tests for InMemoryUserRepository."""

from src.auth.implementation.memory_repo import InMemoryUserRepository
from src.auth.models import User


def test_memory_repository_returns_none_for_unknown_email():
    """A repository with no users returns None for any lookup."""
    repo = InMemoryUserRepository()
    assert repo.get_user_by_email("nobody@gmail.com") is None


def test_memory_repository_stores_and_retrieves_by_email():
    """A user added to the repository can be retrieved by email."""
    repo = InMemoryUserRepository()
    user = User(username="Patrick", email="patrick@gmail.com", password_hash="h")

    repo.add_user(user)

    assert repo.get_user_by_email("patrick@gmail.com") is user
