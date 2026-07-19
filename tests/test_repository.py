"""Unit tests for importer.repository.JsonUserRepository."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from pytest_mock import MockerFixture

from importer.exceptions import DuplicateUserError, RepositoryError
from importer.models import User
from importer.repository import JsonUserRepository


def test_new_repository_starts_empty(db_path: Path) -> None:
    repo = JsonUserRepository(db_path)
    assert len(repo) == 0
    assert not repo.exists("1")


def test_loads_existing_data(populated_db_path: Path) -> None:
    repo = JsonUserRepository(populated_db_path)
    assert len(repo) == 1
    assert repo.exists("1")


def test_add_new_user_succeeds(db_path: Path, sample_user: User) -> None:
    repo = JsonUserRepository(db_path)
    repo.add(sample_user)
    assert repo.exists(sample_user.user_id)
    assert len(repo) == 1


def test_add_duplicate_user_raises(populated_db_path: Path) -> None:
    repo = JsonUserRepository(populated_db_path)
    duplicate = User(user_id="1", name="Someone New", email="new@example.com")
    with pytest.raises(DuplicateUserError) as exc_info:
        repo.add(duplicate)
    assert exc_info.value.user_id == "1"


def test_save_persists_to_disk(db_path: Path, sample_user: User) -> None:
    repo = JsonUserRepository(db_path)
    repo.add(sample_user)
    repo.save()

    assert db_path.exists()
    on_disk = json.loads(db_path.read_text(encoding="utf-8"))
    assert on_disk == {"1": sample_user.to_dict()}


def test_context_manager_saves_on_clean_exit(db_path: Path, sample_user: User) -> None:
    with JsonUserRepository(db_path) as repo:
        repo.add(sample_user)

    assert db_path.exists()
    on_disk = json.loads(db_path.read_text(encoding="utf-8"))
    assert on_disk == {"1": sample_user.to_dict()}


def test_context_manager_does_not_save_on_exception(db_path: Path, sample_user: User) -> None:
    with pytest.raises(ValueError), JsonUserRepository(db_path) as repo:
        repo.add(sample_user)
        raise ValueError("boom")

    assert not db_path.exists()


def test_corrupt_json_raises_repository_error(corrupt_db_path: Path) -> None:
    with pytest.raises(RepositoryError, match="invalid JSON"):
        JsonUserRepository(corrupt_db_path)


def test_non_object_json_raises_repository_error(tmp_path: Path) -> None:
    path = tmp_path / "list_db.json"
    path.write_text("[1, 2, 3]", encoding="utf-8")
    with pytest.raises(RepositoryError, match="JSON object"):
        JsonUserRepository(path)


def test_empty_file_loads_as_empty_store(tmp_path: Path) -> None:
    path = tmp_path / "empty_db.json"
    path.write_text("", encoding="utf-8")
    repo = JsonUserRepository(path)
    assert len(repo) == 0


def test_unreadable_file_raises_repository_error(tmp_path: Path, mocker: MockerFixture) -> None:
    path = tmp_path / "db.json"
    path.write_text("{}", encoding="utf-8")
    mocker.patch.object(Path, "read_text", side_effect=OSError("disk error"))

    with pytest.raises(RepositoryError, match="Could not read"):
        JsonUserRepository(path)


def test_save_failure_raises_repository_error(
    db_path: Path, sample_user: User, mocker: MockerFixture
) -> None:
    repo = JsonUserRepository(db_path)
    repo.add(sample_user)
    mocker.patch.object(Path, "write_text", side_effect=OSError("disk full"))

    with pytest.raises(RepositoryError, match="Could not write"):
        repo.save()
