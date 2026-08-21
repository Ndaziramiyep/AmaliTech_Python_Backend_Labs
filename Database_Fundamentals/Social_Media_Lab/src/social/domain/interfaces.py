"""Protocols implemented by concrete infrastructure/repositories.

Services depend only on these, never on psycopg2/redis/pymongo directly.
`cursor`/`connection` parameters are typed `Any` on purpose: the domain layer
must not import a driver just to name its cursor type.
"""
from __future__ import annotations

from typing import Any, Mapping, Optional, Protocol, Sequence

from social.domain.models import Comment, Follower, Like, Post, User


class UserRepository(Protocol):
    def create(self, cursor: Any, user: User) -> User: ...

    def get_by_id(self, cursor: Any, user_id: int) -> Optional[User]: ...

    def get_by_username(self, cursor: Any, username: str) -> Optional[User]: ...

    def get_by_email(self, cursor: Any, email: str) -> Optional[User]: ...

    def list_all(self, cursor: Any) -> Sequence[User]: ...


class PostRepository(Protocol):
    def create(self, cursor: Any, post: Post) -> Post: ...

    def get_by_id(self, cursor: Any, post_id: int) -> Optional[Post]: ...

    def delete(self, cursor: Any, post_id: int) -> None: ...

    def list_recent(self, cursor: Any, limit: int) -> Sequence[Post]: ...


class CommentRepository(Protocol):
    def create(self, cursor: Any, comment: Comment) -> Comment: ...

    def list_by_post(self, cursor: Any, post_id: int) -> Sequence[Comment]: ...


class FollowerRepository(Protocol):
    def create(self, cursor: Any, follower_id: int, followee_id: int) -> Follower: ...

    def exists(self, cursor: Any, follower_id: int, followee_id: int) -> bool: ...


class LikeRepository(Protocol):
    def create(self, cursor: Any, user_id: int, post_id: int) -> Like: ...

    def exists(self, cursor: Any, user_id: int, post_id: int) -> bool: ...


class FeedRepository(Protocol):
    def get_timeline(self, cursor: Any, follower_id: int, limit: int) -> Sequence[Post]: ...


class Cache(Protocol):
    def get(self, key: str) -> Optional[str]: ...

    def set(self, key: str, value: str, ttl_seconds: int) -> None: ...

    def delete(self, key: str) -> None: ...


class ActivityLogger(Protocol):
    def log(self, activity_type: str, payload: Mapping[str, Any]) -> None: ...


class UnitOfWork(Protocol):
    """Context manager wrapping a single Postgres transaction.

    Repositories are handed `uow.cursor` — they never open a connection or
    call commit()/rollback() themselves.
    """

    @property
    def cursor(self) -> Any: ...

    def __enter__(self) -> "UnitOfWork": ...

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> Optional[bool]: ...

    def commit(self) -> None: ...

    def rollback(self) -> None: ...
