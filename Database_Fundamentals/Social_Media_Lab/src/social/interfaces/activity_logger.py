"""Protocol for the audit trail sink that services depend on instead of importing pymongo directly."""
from __future__ import annotations

from typing import Any, Mapping, Protocol


class ActivityLogger(Protocol):
    """Protocol for a sink that records activity events."""

    def log(self, activity_type: str, payload: Mapping[str, Any]) -> None:
        """Record an activity event with its payload."""
        ...
