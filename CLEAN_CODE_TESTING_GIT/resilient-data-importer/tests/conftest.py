"""Shared pytest fixtures for the resilient data importer test suite."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from importer.models import User

VALID_CSV_CONTENT = (
    "user_id,name,email\n"
    "1,Alice Uwimana,alice@example.com\n"
    "2,Bob Habimana,bob@example.com\n"
    "3,Chantal Mukamana,chantal@example.com\n"
)

MIXED_CSV_CONTENT = (
    "user_id,name,email\n"
    "1,Alice Uwimana,alice@example.com\n"
    "2,,bob@example.com\n"
    "3,Chantal Mukamana,not-an-email\n"
    "1,Alice Duplicate,alice2@example.com\n"
    "4,David Ndayisenga,david@example.com\n"
)


@pytest.fixture
def sample_user() -> User:
    """A single, valid, ready-to-use :class:`User` instance."""
    return User(user_id="1", name="Alice Uwimana", email="alice@example.com")


@pytest.fixture
def valid_csv_path(tmp_path: Path) -> Path:
    """Path to a temporary CSV file containing only valid rows."""
    csv_path = tmp_path / "users_valid.csv"
    csv_path.write_text(VALID_CSV_CONTENT, encoding="utf-8")
    return csv_path


@pytest.fixture
def mixed_csv_path(tmp_path: Path) -> Path:
    """Path to a temporary CSV file with a mix of valid/invalid/duplicate rows."""
    csv_path = tmp_path / "users_mixed.csv"
    csv_path.write_text(MIXED_CSV_CONTENT, encoding="utf-8")
    return csv_path


@pytest.fixture
def empty_csv_path(tmp_path: Path) -> Path:
    """Path to a temporary, completely empty CSV file."""
    csv_path = tmp_path / "empty.csv"
    csv_path.write_text("", encoding="utf-8")
    return csv_path


@pytest.fixture
def missing_column_csv_path(tmp_path: Path) -> Path:
    """Path to a temporary CSV file missing the required 'email' column."""
    csv_path = tmp_path / "missing_column.csv"
    csv_path.write_text("user_id,name\n1,Alice Uwimana\n", encoding="utf-8")
    return csv_path


@pytest.fixture
def missing_csv_path(tmp_path: Path) -> Path:
    """Path to a CSV file that does not exist on disk."""
    return tmp_path / "does_not_exist.csv"


@pytest.fixture
def db_path(tmp_path: Path) -> Path:
    """Path to a JSON database file that does not exist yet."""
    return tmp_path / "db.json"


@pytest.fixture
def populated_db_path(tmp_path: Path) -> Path:
    """Path to a JSON database file pre-populated with one user (id '1')."""
    path = tmp_path / "db_populated.json"
    path.write_text(
        json.dumps(
            {"1": {"user_id": "1", "name": "Existing User", "email": "existing@example.com"}}
        ),
        encoding="utf-8",
    )
    return path


@pytest.fixture
def corrupt_db_path(tmp_path: Path) -> Path:
    """Path to a JSON database file containing invalid JSON."""
    path = tmp_path / "db_corrupt.json"
    path.write_text("{not valid json", encoding="utf-8")
    return path
