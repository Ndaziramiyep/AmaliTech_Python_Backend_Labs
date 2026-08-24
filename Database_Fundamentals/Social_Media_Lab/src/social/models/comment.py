"""Comment domain model."""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(frozen=True, slots=True)
class Comment:
    """Represents a comment left on a post."""

    id: Optional[int]
    post_id: int
    author_id: int
    body: str
    created_at: Optional[datetime] = None
