"""Protocols for Postgres-backed repositories, typed with `cursor: Any` so this module never needs to import a driver, that services depend on instead of psycopg2 directly."""
from __future__ import annotations

from typing import Any, Mapping, Optional, Protocol, Sequence

from social.models import Comment, Follower, Like, Post, User


class UserRepository(Protocol):
    """Protocol for persisting and retrieving user records."""

    def create(self, cursor: Any, user: User) -> User:
        """Insert a new user and return the stored record."""
        ...

    def get_by_id(self, cursor: Any, user_id: int) -> Optional[User]:
        """Return the user with the given id, or None if not found."""
        ...

    def get_by_username(self, cursor: Any, username: str) -> Optional[User]:
        """Return the user with the given username, or None if not found."""
        ...

    def get_by_email(self, cursor: Any, email: str) -> Optional[User]:
        """Return the user with the given email, or None if not found."""
        ...

    def list_all(self, cursor: Any) -> Sequence[User]:
        """Return all users."""
        ...

    def update_profile(
        self, cursor: Any, user_id: int, full_name: str, bio: str
    ) -> Optional[User]:
        """Update a user's full name and bio, returning the updated record or None if not found."""
        ...


class PostRepository(Protocol):
    """Protocol for persisting and retrieving post records."""

    def create(self, cursor: Any, post: Post) -> Post:
        """Insert a new post and return the stored record."""
        ...

    def get_by_id(self, cursor: Any, post_id: int) -> Optional[Post]:
        """Return the post with the given id, or None if not found."""
        ...

    def delete(self, cursor: Any, post_id: int) -> None:
        """Delete the post with the given id."""
        ...

    def list_recent(self, cursor: Any, limit: int) -> Sequence[Post]:
        """Return the most recent posts up to the given limit."""
        ...


class CommentRepository(Protocol):
    """Protocol for persisting and retrieving comments on posts."""

    def create(self, cursor: Any, comment: Comment) -> Comment:
        """Insert a new comment and return the stored record."""
        ...

    def list_by_post(self, cursor: Any, post_id: int) -> Sequence[Comment]:
        """Return all comments for a given post."""
        ...

    def count_by_posts(self, cursor: Any, post_ids: Sequence[int]) -> Mapping[int, int]:
        """Return the comment count for each of the given post ids."""
        ...


class FollowerRepository(Protocol):
    """Protocol for managing follower relationships between users."""

    def create(self, cursor: Any, follower_id: int, followee_id: int) -> Follower:
        """Create a follow relationship between two users."""
        ...

    def exists(self, cursor: Any, follower_id: int, followee_id: int) -> bool:
        """Return whether a follow relationship exists between two users."""
        ...

    def delete(self, cursor: Any, follower_id: int, followee_id: int) -> bool:
        """Remove a follow relationship between two users, returning whether it existed."""
        ...

    def list_following(self, cursor: Any, follower_id: int) -> Sequence[int]:
        """Return the ids of users a given user follows."""
        ...

    def list_followers(self, cursor: Any, followee_id: int) -> Sequence[int]:
        """Return the ids of users following a given user."""
        ...


class LikeRepository(Protocol):
    """Protocol for persisting and retrieving likes on posts."""

    def create(self, cursor: Any, user_id: int, post_id: int) -> Like:
        """Record a like from a user on a post."""
        ...

    def exists(self, cursor: Any, user_id: int, post_id: int) -> bool:
        """Return whether a user has liked a post."""
        ...

    def count_by_posts(self, cursor: Any, post_ids: Sequence[int]) -> Mapping[int, int]:
        """Return the like count for each of the given post ids."""
        ...


class FeedRepository(Protocol):
    """Protocol for retrieving a user's timeline feed."""

    def get_timeline(self, cursor: Any, follower_id: int, limit: int) -> Sequence[Post]:
        """Return the timeline of posts for a given follower, up to the given limit."""
        ...
