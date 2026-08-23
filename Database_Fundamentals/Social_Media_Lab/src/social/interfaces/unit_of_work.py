"""Protocol for a single Postgres transaction boundary."""
from __future__ import annotations

from typing import Any, Optional, Protocol


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
