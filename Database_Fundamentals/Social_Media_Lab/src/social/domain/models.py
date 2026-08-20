"""Pure dataclasses describing the domain. No I/O, no driver imports."""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Mapping, Optional


@dataclass(frozen=True, slots=True)
class User:
    id: Optional[int]
    username: str
    email: str
    created_at: Optional[datetime] = None


@dataclass(frozen=True, slots=True)
class Post:
    id: Optional[int]
    author_id: int
    body: str
    metadata: Mapping[str, Any] = field(default_factory=dict)
    created_at: Optional[datetime] = None


@dataclass(frozen=True, slots=True)
class Comment:
    id: Optional[int]
    post_id: int
    author_id: int
    body: str
    created_at: Optional[datetime] = None


@dataclass(frozen=True, slots=True)
class Follower:
    follower_id: int
    followee_id: int
    created_at: Optional[datetime] = None


@dataclass(frozen=True, slots=True)
class Like:
    user_id: int
    post_id: int
    created_at: Optional[datetime] = None
