# tests/test_interfaces_coverage.py
from src.auth.interfaces import PasswordHasher, UserRepository
from src.auth.models import User


# Minimal concrete classes just for coverage
class DummyRepo(UserRepository):
    def get_by_email(self, email: str):
        return None

    def add(self, user: User):
        pass


class DummyHasher(PasswordHasher):
    def hash_password(self, password: str):
        return "hashed"

    def verify_password(self, password: str, hashed: str):
        return True


def test_interfaces_dummy_execution():
    repo = DummyRepo()
    hasher = DummyHasher()
    user = User(username="test", email="test@example.com", password_hash="hash")
    repo.add(user)
    repo.get_by_email("anything")
    hasher.hash_password("pass")
    hasher.verify_password("pass", "hashed")
