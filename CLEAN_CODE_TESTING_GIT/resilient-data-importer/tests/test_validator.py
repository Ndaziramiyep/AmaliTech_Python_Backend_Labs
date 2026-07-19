"""Unit tests for importer.validator.UserRowValidator."""

from __future__ import annotations

import pytest

from importer.exceptions import RowValidationError
from importer.models import User
from importer.validator import UserRowValidator


@pytest.fixture
def validator() -> UserRowValidator:
    return UserRowValidator()


@pytest.mark.parametrize(
    "raw_row",
    [
        {"user_id": "1", "name": "Alice", "email": "alice@example.com"},
        {"user_id": " 2 ", "name": " Bob ", "email": " bob@example.com "},
        {"user_id": "3", "name": "O'Brien", "email": "obrien@sub.example.co.uk"},
    ],
)
def test_valid_rows_produce_user(validator: UserRowValidator, raw_row: dict[str, str]) -> None:
    user = validator.validate(1, raw_row)
    assert isinstance(user, User)
    assert user.user_id == raw_row["user_id"].strip()
    assert user.name == raw_row["name"].strip()
    assert user.email == raw_row["email"].strip()


@pytest.mark.parametrize(
    ("raw_row", "expected_reason"),
    [
        ({"user_id": "", "name": "Alice", "email": "alice@example.com"}, "user_id"),
        ({"user_id": "1", "name": "", "email": "alice@example.com"}, "name"),
        ({"user_id": "1", "name": "Alice", "email": ""}, "email"),
        ({"user_id": "1", "name": "Alice", "email": "not-an-email"}, "invalid email"),
        ({"user_id": "1", "name": "Alice", "email": "missing-at-sign.com"}, "invalid email"),
        ({"user_id": "1", "name": "Alice", "email": "no-domain@"}, "invalid email"),
        ({"user_id": "   ", "name": "Alice", "email": "alice@example.com"}, "user_id"),
    ],
)
def test_invalid_rows_raise_row_validation_error(
    validator: UserRowValidator, raw_row: dict[str, str], expected_reason: str
) -> None:
    with pytest.raises(RowValidationError) as exc_info:
        validator.validate(7, raw_row)

    assert exc_info.value.row_number == 7
    assert expected_reason in str(exc_info.value)


def test_missing_keys_are_treated_as_blank(validator: UserRowValidator) -> None:
    with pytest.raises(RowValidationError, match="user_id"):
        validator.validate(1, {"name": "Alice", "email": "alice@example.com"})
