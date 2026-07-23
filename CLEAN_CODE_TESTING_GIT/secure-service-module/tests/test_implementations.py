"""Tests for the concrete UserRepository and PasswordHasher implementations."""

from src.auth.implementation.bcrypt_hasher import BcryptPasswordHasher
from src.auth.implementation.memory_repo import InMemoryUserRepository
from src.auth.models import User


def test_memory_repository_returns_none_for_unknown_email():
    """A repository with no users returns None for any lookup."""
    repo = InMemoryUserRepository()
    assert repo.get_by_email("nobody@gmail.com") is None


def test_memory_repository_stores_and_retrieves_by_email():
    """A user added to the repository can be retrieved by email."""
    repo = InMemoryUserRepository()
    user = User(username="Patrick", email="patrick@gmail.com", password_hash="h")

    repo.add(user)

    assert repo.get_by_email("patrick@gmail.com") is user


def test_bcrypt_hasher_produces_a_different_string_than_the_password():
    """Hashing a password never returns the plain-text password itself."""
    hasher = BcryptPasswordHasher()

    hashed = hasher.hash_password("SecurePass1")

    assert hashed != "SecurePass1"


def test_bcrypt_hasher_verifies_the_correct_password():
    """A password verifies successfully against its own bcrypt hash."""
    hasher = BcryptPasswordHasher()
    hashed = hasher.hash_password("SecurePass1")

    assert hasher.verify_password("SecurePass1", hashed) is True


def test_bcrypt_hasher_rejects_the_wrong_password():
    """A different password fails verification against an existing hash."""
    hasher = BcryptPasswordHasher()
    hashed = hasher.hash_password("SecurePass1")

    assert hasher.verify_password("WrongPassword", hashed) is False
