"""One row of a user's timeline feed."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from social_platform.features.posts.model import PostMetadata


@dataclass(frozen=True, slots=True)
class FeedPostEntry:
    """One page row of a user's timeline feed, including the author's username."""

    post_id: int
    author_user_id: int
    author_username: str
    content: str
    metadata: PostMetadata
    created_at: datetime
