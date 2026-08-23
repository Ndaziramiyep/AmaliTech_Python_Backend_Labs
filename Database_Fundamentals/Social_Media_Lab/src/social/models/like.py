"""Like domain model."""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(frozen=True, slots=True)
class Like:
    user_id: int
    post_id: int
    created_at: Optional[datetime] = None
