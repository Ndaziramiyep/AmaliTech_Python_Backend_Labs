"""Data models for the auth module."""

import uuid
from dataclasses import dataclass, field


@dataclass
class User:
    """A registered user."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    username: str = ""
    email: str = ""
    password_hash: str = ""
