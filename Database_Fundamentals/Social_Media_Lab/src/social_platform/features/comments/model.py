"""The comment entity, and a display entry for one node in a comment thread."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class Comment:
    """A comment left by a user on a post, optionally itself a reply to another comment."""

    comment_id: int
    post_id: int
    commenter_user_id: int
    parent_comment_id: int | None
    content: str
    created_at: datetime


@dataclass(frozen=True, slots=True)
class CommentThreadEntry:
    """One comment within a post's full thread, with its nesting depth for display.

    Top-level comments have `depth` 0; a reply to a top-level comment has `depth` 1,
    a reply to that reply has `depth` 2, and so on -- however deep the conversation goes.
    """

    comment: Comment
    depth: int
