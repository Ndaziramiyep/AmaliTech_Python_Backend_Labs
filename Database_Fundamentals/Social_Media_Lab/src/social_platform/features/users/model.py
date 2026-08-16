"""The user entity."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class User:
    """A registered platform user (never carries a password hash)."""

    user_id: int
    username: str
    email: str
    display_name: str
    created_at: datetime
