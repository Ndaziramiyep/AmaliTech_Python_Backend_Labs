"""Protocol for the audit trail sink. Services depend only on this, never
on pymongo directly.
"""
from __future__ import annotations

from typing import Any, Mapping, Protocol


class ActivityLogger(Protocol):
    def log(self, activity_type: str, payload: Mapping[str, Any]) -> None: ...
