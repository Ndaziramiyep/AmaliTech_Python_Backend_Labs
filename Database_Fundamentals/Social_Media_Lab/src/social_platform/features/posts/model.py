"""The post entity and its JSONB metadata shape."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import TypedDict


class PostMetadata(TypedDict, total=False):
    """Free-form JSONB payload stored alongside a post: tags and location."""

    tags: list[str]
    location: str


@dataclass(frozen=True, slots=True)
class Post:
    """A single post authored by a user."""

    post_id: int
    author_user_id: int
    content: str
    metadata: PostMetadata
    created_at: datetime
