"""Follower edge domain model (self-referencing user follow relationship)."""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(frozen=True, slots=True)
class Follower:
    """Represents a follow relationship between two users."""

    follower_id: int
    followee_id: int
    created_at: Optional[datetime] = None
