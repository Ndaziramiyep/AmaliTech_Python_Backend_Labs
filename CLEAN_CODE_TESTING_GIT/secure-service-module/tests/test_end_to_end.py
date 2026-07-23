"""End-to-end test using the real bcrypt hasher and in-memory repository."""

from src.auth.implementation.bcrypt_hasher import BcryptPasswordHasher
from src.auth.implementation.memory_repo import InMemoryUserRepository
from src.auth.service import UserService


def test_end_to_end_registration_and_login():
    """Register and log in a real user with bcrypt hashing and in-memory storage."""
    service = UserService(InMemoryUserRepository(), BcryptPasswordHasher())

    user = service.register_user("Patrick", "patrick@gmail.com", "SecurePass1")

    assert user.username == "Patrick"
    assert user.password_hash != "SecurePass1"
    assert service.verify_user("patrick@gmail.com", "SecurePass1") is True
