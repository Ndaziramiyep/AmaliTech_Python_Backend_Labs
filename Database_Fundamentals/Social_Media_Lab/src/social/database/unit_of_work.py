"""Transaction boundary where entering the `with` block is the implicit BEGIN and `__exit__` rolls back automatically if the caller raised instead of committing."""
from types import TracebackType
from typing import Any, Optional

from social.database.connection_pool import PostgresConnectionPool
from social.exceptions import UnitOfWorkStateError


class PostgresUnitOfWork:
    """Manages one Postgres connection and cursor as a single commit-or-rollback transaction."""

    def __init__(self, pool: PostgresConnectionPool) -> None:
        """Store the connection pool this unit of work will acquire a connection from."""
        self._pool = pool
        self._connection: Optional[Any] = None
        self._cursor: Optional[Any] = None

    @property
    def cursor(self) -> Any:
        """Return the active cursor, raising if used outside the context manager."""
        if self._cursor is None:
            raise UnitOfWorkStateError("UnitOfWork must be used as a context manager")
        return self._cursor

    def __enter__(self) -> "PostgresUnitOfWork":
        """Acquire a connection and cursor from the pool and return this unit of work."""
        self._connection = self._pool.get_connection()
        self._cursor = self._connection.cursor()
        return self

    def commit(self) -> None:
        """Commit the current transaction."""
        self._connection.commit()

    def rollback(self) -> None:
        """Roll back the current transaction."""
        self._connection.rollback()

    def __exit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc: Optional[BaseException],
        tb: Optional[TracebackType],
    ) -> None:
        """Roll back on exception, then release the connection back to the pool, discarding it if the rollback itself failed."""
        discard = False
        try:
            if exc_type is not None:
                self.rollback()
        except Exception:
            discard = True
        finally:
            self._cursor.close()
            self._pool.release_connection(self._connection, discard=discard)
            self._cursor = None
            self._connection = None
        return None
