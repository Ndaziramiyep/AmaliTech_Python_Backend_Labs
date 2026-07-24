"""Compliance tests proving concrete classes can satisfy the auth ABCs."""

from typing import Optional

import pytest

from src.auth.interfaces import PasswordHasher, UserRepository
from src.auth.models import User


class _DummyRepository(UserRepository):
    def get_by_email(self, email: str) -> Optional[User]:
        return None

    def add(self, user: User) -> None:
        pass


class _DummyHasher(PasswordHasher):
    def hash_password(self, password: str) -> str:
        return "hashed"

    def verify_password(self, password: str, hashed: str) -> bool:
        return True


def test_user_repository_cannot_be_instantiated_directly():
    """UserRepository is abstract and cannot be instantiated on its own."""
    with pytest.raises(TypeError):
        UserRepository()  # type: ignore[abstract]


def test_password_hasher_cannot_be_instantiated_directly():
    """PasswordHasher is abstract and cannot be instantiated on its own."""
    with pytest.raises(TypeError):
        PasswordHasher()  # type: ignore[abstract]


def test_concrete_repository_satisfies_the_contract():
    """A concrete UserRepository subclass can be constructed and used."""
    repo = _DummyRepository()
    user = User(username="Patrick", email="patrick@gmail.com", password_hash="h")

    repo.add(user)
    assert repo.get_by_email("patrick@gmail.com") is None


def test_concrete_hasher_satisfies_the_contract():
    """A concrete PasswordHasher subclass can be constructed and used."""
    hasher = _DummyHasher()

    assert hasher.hash_password("secret") == "hashed"
    assert hasher.verify_password("secret", "hashed") is True
