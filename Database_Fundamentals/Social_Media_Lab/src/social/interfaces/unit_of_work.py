"""Protocol for a single Postgres transaction boundary."""
from __future__ import annotations

from typing import Any, Optional, Protocol


class UnitOfWork(Protocol):
    """Context manager wrapping a single Postgres transaction whose cursor is handed to repositories that never open connections or call commit()/rollback() themselves."""

    @property
    def cursor(self) -> Any:
        """Return the cursor for the current transaction."""
        ...

    def __enter__(self) -> "UnitOfWork":
        """Begin the transaction and return the unit of work."""
        ...

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> Optional[bool]:
        """End the transaction, rolling back if an exception occurred."""
        ...

    def commit(self) -> None:
        """Commit the current transaction."""
        ...

    def rollback(self) -> None:
        """Roll back the current transaction."""
        ...
