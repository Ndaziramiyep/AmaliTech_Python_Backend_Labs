"""Tests for the User data model."""

from src.auth.models import User


def test_user_has_expected_fields():
    """A User stores id, username, email, and password_hash."""
    user = User(username="Patrick", email="patrick@gmail.com", password_hash="hashed")

    assert user.username == "Patrick"
    assert user.email == "patrick@gmail.com"
    assert user.password_hash == "hashed"
    assert isinstance(user.id, str)
    assert user.id


def test_user_ids_are_unique_by_default():
    """Two users created without an explicit id get distinct UUIDs."""
    first = User(username="A", email="a@example.com", password_hash="x")
    second = User(username="B", email="b@example.com", password_hash="y")

    assert first.id != second.id
