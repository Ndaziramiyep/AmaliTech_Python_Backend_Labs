"""Unit tests for importer.models."""

from __future__ import annotations

import dataclasses

import pytest

from importer.models import User


def test_user_to_dict_round_trips_fields(sample_user: User) -> None:
    assert sample_user.to_dict() == {
        "user_id": "1",
        "name": "Alice Uwimana",
        "email": "alice@example.com",
    }


def test_user_is_immutable(sample_user: User) -> None:
    with pytest.raises(dataclasses.FrozenInstanceError):
        sample_user.name = "Someone Else"  # type: ignore[misc]


def test_user_equality_by_value() -> None:
    a = User(user_id="1", name="Alice", email="alice@example.com")
    b = User(user_id="1", name="Alice", email="alice@example.com")
    assert a == b
