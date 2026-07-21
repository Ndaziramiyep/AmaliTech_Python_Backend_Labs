"""End-to-end integration test using real implementations."""

from src.auth.implementation.bcrypt_hasher import BcryptPasswordHasher
from src.auth.implementation.memory_repo import InMemoryUserRepository
from src.auth.service import UserService


def test_end_to_end_registration_and_login():
    """Register and log in a real user with bcrypt hashing and in-memory storage."""
    repo = InMemoryUserRepository()
    hasher = BcryptPasswordHasher()
    service = UserService(repo, hasher)

    user = service.register_user("Patrick", "patrick@example.com", "Patrick")
    assert user.username == "Patrick"
    assert user.password_hash != "Patrick"
    assert service.verify_user("patrick@example.com", "Patrick") is True
