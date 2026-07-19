import json
import os

import pytest
from src.exceptions import DatabaseError, DuplicateUserError
from src.models.user import User
from src.storage import UserRepository


@pytest.fixture
def empty_database(tmp_path):
    db_file = tmp_path / "database.json"
    db_file.write_text("{}")
    return str(db_file)


@pytest.fixture
def filled_database(tmp_path):
    db_file = tmp_path / "database.json"
    users = {"1": {"name": "John Doe", "email": "john.doe@example.com"}}
    db_file.write_text(json.dumps(users))
    return str(db_file)


def test_add_user_success(empty_database):
    repo = UserRepository(db_path=empty_database)
    user = User(user_id=1, name="John Doe", email="john.doe@example.com")
    repo.add_user(user)

    with open(empty_database, "r") as f:
        data = json.load(f)

    assert "1" in data
    assert data["1"]["name"] == "John Doe"


def test_add_duplicate_user(filled_database):
    repo = UserRepository(db_path=filled_database)
    user = User(user_id=1, name="Jane Smith", email="jane.smith@example.com")
    with pytest.raises(DuplicateUserError):
        repo.add_user(user)


def test_user_exists(filled_database):
    repo = UserRepository(db_path=filled_database)
    assert repo.user_exists(1) is True
    assert repo.user_exists(2) is False


def test_database_error_on_read_only_db(tmp_path):
    db_file = tmp_path / "readonly.json"
    db_file.write_text("{}")
    os.chmod(db_file, 0o444)  # read-only

    repo = UserRepository(db_path=str(db_file))
    user = User(user_id=1, name="Jane Smith", email="jane.smith@example.com")

    with pytest.raises(DatabaseError):
        repo.add_user(user)

    os.chmod(db_file, 0o666)  # restore write permissions


def test_load_database_file_not_found(tmp_path):
    missing_file = tmp_path / "missing.json"
    repo = UserRepository(db_path=str(missing_file))
    # It should create empty users dict without exception
    assert repo.users == {}


def test_load_database_json_decode_error(tmp_path):
    bad_file = tmp_path / "bad.json"
    bad_file.write_text("{ invalid json }")
    repo = UserRepository(db_path=str(bad_file))
    # Should fallback to empty dict
    assert repo.users == {}
