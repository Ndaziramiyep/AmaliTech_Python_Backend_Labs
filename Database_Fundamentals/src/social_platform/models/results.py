"""Outcome enums for idempotent write operations."""

from __future__ import annotations

from enum import Enum


class FollowResult(Enum):
    """Outcome of attempting to create a follow relationship."""

    CREATED = "created"
    ALREADY_EXISTS = "already_exists"


class UnfollowResult(Enum):
    """Outcome of attempting to remove a follow relationship."""

    REMOVED = "removed"
    DID_NOT_EXIST = "did_not_exist"
