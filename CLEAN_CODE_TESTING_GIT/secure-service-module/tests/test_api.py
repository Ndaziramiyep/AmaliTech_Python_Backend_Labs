"""Tests for the thin FastAPI wrapper around UserService."""

import pytest
from fastapi.testclient import TestClient

from src.api.main import app, get_user_service


@pytest.fixture(autouse=True)
def _isolated_user_service():
    """Clear the cached UserService before each test for isolation."""
    get_user_service.cache_clear()
    yield
    get_user_service.cache_clear()


@pytest.fixture
def client():
    return TestClient(app)


def test_register_returns_201_with_the_created_user(client):
    """A successful registration returns 201 with username, email, and id."""
    response = client.post(
        "/register",
        json={
            "username": "Patrick",
            "email": "patrick@gmail.com",
            "password": "SecurePass1",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["username"] == "Patrick"
    assert body["email"] == "patrick@gmail.com"
    assert "id" in body
    assert "password" not in body


def test_register_duplicate_email_returns_409(client):
    """Registering the same email twice returns 409 Conflict."""
    payload = {
        "username": "Patrick",
        "email": "patrick@gmail.com",
        "password": "SecurePass1",
    }
    client.post("/register", json=payload)

    response = client.post("/register", json=payload)

    assert response.status_code == 409


def test_register_short_password_returns_400(client):
    """Registering with a too-short password returns 400 Bad Request."""
    response = client.post(
        "/register",
        json={"username": "Patrick", "email": "patrick@gmail.com", "password": "short"},
    )

    assert response.status_code == 400


def test_register_malformed_email_returns_400(client):
    """Registering with a malformed email returns 400 Bad Request."""
    response = client.post(
        "/register",
        json={
            "username": "Patrick",
            "email": "not-an-email",
            "password": "SecurePass1",
        },
    )

    assert response.status_code == 400


def test_login_success_returns_200(client):
    """Verifying correct credentials for a registered user returns 200."""
    client.post(
        "/register",
        json={
            "username": "Patrick",
            "email": "patrick@gmail.com",
            "password": "SecurePass1",
        },
    )

    response = client.post(
        "/login",
        json={"email": "patrick@gmail.com", "password": "SecurePass1"},
    )

    assert response.status_code == 200
    assert response.json() == {"success": True}


def test_login_unknown_email_returns_404(client):
    """Logging in with an unregistered email returns 404 Not Found."""
    response = client.post(
        "/login",
        json={"email": "unknown@gmail.com", "password": "SecurePass1"},
    )

    assert response.status_code == 404


def test_login_wrong_password_returns_401(client):
    """Logging in with the wrong password returns 401 Unauthorized."""
    client.post(
        "/register",
        json={
            "username": "Patrick",
            "email": "patrick@gmail.com",
            "password": "SecurePass1",
        },
    )

    response = client.post(
        "/login",
        json={"email": "patrick@gmail.com", "password": "WrongPassword"},
    )

    assert response.status_code == 401
