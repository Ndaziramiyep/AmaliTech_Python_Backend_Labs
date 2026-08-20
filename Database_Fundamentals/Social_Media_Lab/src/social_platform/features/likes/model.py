"""The outcome enums for the idempotent like/unlike operations."""

from __future__ import annotations

from enum import Enum


class LikeResult(Enum):
    """Outcome of attempting to like a post."""

    CREATED = "created"
    ALREADY_EXISTS = "already_exists"


class UnlikeResult(Enum):
    """Outcome of attempting to remove a like."""

    REMOVED = "removed"
    DID_NOT_EXIST = "did_not_exist"
