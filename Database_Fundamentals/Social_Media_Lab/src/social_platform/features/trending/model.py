"""One ranked row of the trending-posts query."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from social_platform.features.posts.model import PostMetadata


@dataclass(frozen=True, slots=True)
class TrendingPostEntry:
    """One ranked row of the trending-posts query, including its comment count."""

    post_id: int
    author_user_id: int
    content: str
    metadata: PostMetadata
    created_at: datetime
    comment_count: int
