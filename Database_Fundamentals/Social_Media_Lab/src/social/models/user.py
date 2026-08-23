"""User domain model."""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass(frozen=True, slots=True)
class User:
    id: Optional[int]
    username: str
    email: str
    password_hash: str = field(repr=False)
    created_at: Optional[datetime] = None
    full_name: str = ""
    bio: str = ""
    is_active: bool = True
