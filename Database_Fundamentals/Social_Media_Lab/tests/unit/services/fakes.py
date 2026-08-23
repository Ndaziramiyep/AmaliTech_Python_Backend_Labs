"""In-memory stand-ins for the domain Protocols, used to unit-test services
without a real Postgres/Redis/Mongo. FakeUnitOfWork mirrors the control flow
of PostgresUnitOfWork exactly (rollback on unhandled exception, exception
never suppressed) so a passing test is actually exercising that invariant,
not just recording calls.
"""
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from social.models import Comment, Follower, Like, Post, User


class FakeUnitOfWork:
    def __init__(self) -> None:
        self.entered = False
        self.committed = False
        self.rolled_back = False
        self._cursor = object()

    @property
    def cursor(self) -> Any:
        return self._cursor

    def __enter__(self) -> "FakeUnitOfWork":
        self.entered = True
        return self

    def commit(self) -> None:
        self.committed = True

    def rollback(self) -> None:
        self.rolled_back = True

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        if exc_type is not None:
            self.rollback()
        return None


class FakeFollowerRepository:
    def __init__(self, *, raise_error: Optional[Exception] = None) -> None:
        self._raise_error = raise_error
        self.calls: List[Tuple[int, int]] = []
        self.received_cursor: Any = None

    def create(self, cursor: Any, follower_id: int, followee_id: int) -> Follower:
        self.received_cursor = cursor
        self.calls.append((follower_id, followee_id))
        if self._raise_error is not None:
            raise self._raise_error
        return Follower(follower_id=follower_id, followee_id=followee_id, created_at=None)

    def exists(self, cursor: Any, follower_id: int, followee_id: int) -> bool:
        return (follower_id, followee_id) in self.calls


class FakeLikeRepository:
    def __init__(self, *, raise_error: Optional[Exception] = None) -> None:
        self._raise_error = raise_error
        self.calls: List[Tuple[int, int]] = []
        self.received_cursor: Any = None

    def create(self, cursor: Any, user_id: int, post_id: int) -> Like:
        self.received_cursor = cursor
        self.calls.append((user_id, post_id))
        if self._raise_error is not None:
            raise self._raise_error
        return Like(user_id=user_id, post_id=post_id, created_at=None)

    def exists(self, cursor: Any, user_id: int, post_id: int) -> bool:
        return (user_id, post_id) in self.calls

    def count_by_posts(self, cursor: Any, post_ids: Sequence[int]) -> Mapping[int, int]:
        counts: Dict[int, int] = {}
        for _, liked_post_id in self.calls:
            if liked_post_id in post_ids:
                counts[liked_post_id] = counts.get(liked_post_id, 0) + 1
        return counts


class FakePostRepository:
    def __init__(self, *, raise_error: Optional[Exception] = None) -> None:
        self._raise_error = raise_error
        self.calls: List[Post] = []
        self.received_cursor: Any = None
        self._next_id = 1

    def create(self, cursor: Any, post: Post) -> Post:
        self.received_cursor = cursor
        if self._raise_error is not None:
            raise self._raise_error
        created = Post(
            id=self._next_id,
            author_id=post.author_id,
            body=post.body,
            metadata=post.metadata,
            created_at=None,
        )
        self._next_id += 1
        self.calls.append(created)
        return created

    def get_by_id(self, cursor: Any, post_id: int) -> Optional[Post]:
        return next((p for p in self.calls if p.id == post_id), None)

    def delete(self, cursor: Any, post_id: int) -> None:
        self.calls = [p for p in self.calls if p.id != post_id]

    def list_recent(self, cursor: Any, limit: int) -> Sequence[Post]:
        self.received_cursor = cursor
        return list(reversed(self.calls))[:limit]


class FakeCommentRepository:
    def __init__(self, *, raise_error: Optional[Exception] = None) -> None:
        self._raise_error = raise_error
        self.calls: List[Comment] = []
        self.received_cursor: Any = None
        self._next_id = 1

    def create(self, cursor: Any, comment: Comment) -> Comment:
        self.received_cursor = cursor
        self.calls.append(comment)
        if self._raise_error is not None:
            raise self._raise_error
        created = Comment(
            id=self._next_id,
            post_id=comment.post_id,
            author_id=comment.author_id,
            body=comment.body,
            created_at=None,
        )
        self._next_id += 1
        return created

    def list_by_post(self, cursor: Any, post_id: int) -> Sequence[Comment]:
        self.received_cursor = cursor
        return [c for c in self.calls if c.post_id == post_id]

    def count_by_posts(self, cursor: Any, post_ids: Sequence[int]) -> Mapping[int, int]:
        counts: Dict[int, int] = {}
        for comment in self.calls:
            if comment.post_id in post_ids:
                counts[comment.post_id] = counts.get(comment.post_id, 0) + 1
        return counts


class FakeUserRepository:
    def __init__(self, *, raise_error: Optional[Exception] = None) -> None:
        self._raise_error = raise_error
        self.calls: List[User] = []
        self.received_cursor: Any = None
        self._next_id = 1

    def create(self, cursor: Any, user: User) -> User:
        self.received_cursor = cursor
        if self._raise_error is not None:
            raise self._raise_error
        created = User(
            id=self._next_id,
            username=user.username,
            email=user.email,
            password_hash=user.password_hash,
            created_at=None,
        )
        self._next_id += 1
        self.calls.append(created)
        return created

    def get_by_id(self, cursor: Any, user_id: int) -> Optional[User]:
        return next((u for u in self.calls if u.id == user_id), None)

    def get_by_username(self, cursor: Any, username: str) -> Optional[User]:
        return next((u for u in self.calls if u.username == username), None)

    def get_by_email(self, cursor: Any, email: str) -> Optional[User]:
        return next((u for u in self.calls if u.email == email), None)

    def list_all(self, cursor: Any) -> Sequence[User]:
        self.received_cursor = cursor
        return list(self.calls)


class FakeFeedRepository:
    def __init__(self, *, posts: Optional[List[Post]] = None) -> None:
        self.posts = posts or []
        self.calls: List[Tuple[int, int]] = []
        self.received_cursor: Any = None

    def get_timeline(self, cursor: Any, follower_id: int, limit: int) -> Sequence[Post]:
        self.received_cursor = cursor
        self.calls.append((follower_id, limit))
        return self.posts[:limit]


class FakeCache:
    def __init__(self) -> None:
        self._store: Dict[str, str] = {}
        self.deleted_keys: List[str] = []

    def get(self, key: str) -> Optional[str]:
        return self._store.get(key)

    def set(self, key: str, value: str, ttl_seconds: int) -> None:
        self._store[key] = value

    def delete(self, key: str) -> None:
        self.deleted_keys.append(key)
        self._store.pop(key, None)


class FakeActivityLogger:
    def __init__(self) -> None:
        self.entries: List[Tuple[str, Mapping[str, Any]]] = []

    def log(self, activity_type: str, payload: Mapping[str, Any]) -> None:
        self.entries.append((activity_type, dict(payload)))
