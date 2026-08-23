"""Post domain model."""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Mapping, Optional


@dataclass(frozen=True, slots=True)
class Post:
    id: Optional[int]
    author_id: int
    body: str
    metadata: Mapping[str, Any] = field(default_factory=dict)
    created_at: Optional[datetime] = None
