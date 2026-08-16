"""The comment entity."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class Comment:
    """A comment left by a user on a post."""

    comment_id: int
    post_id: int
    commenter_user_id: int
    content: str
    created_at: datetime
