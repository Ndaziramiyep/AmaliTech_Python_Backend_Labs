"""The user profile: a user's public info plus their activity counts."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class UserProfile:
    """A user's public profile: their info plus post/follower/following counts.

    Composed on read from three features (`users`, `posts`, `followers`) rather than
    stored anywhere of its own -- there is no `profiles` table, just a view over data
    that already lives in `users`, `posts`, and `followers`.
    """

    user_id: int
    username: str
    bio: str | None
    post_count: int
    follower_count: int
    following_count: int
