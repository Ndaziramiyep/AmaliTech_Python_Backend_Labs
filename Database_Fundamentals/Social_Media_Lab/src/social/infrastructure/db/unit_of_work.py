"""Transaction boundary: one connection, one cursor, one commit or rollback.

psycopg2 opens a transaction implicitly on the first statement, so there is
no explicit BEGIN here — entering the `with` block is the BEGIN, `commit()`/
`rollback()` end it, and `__exit__` rolls back automatically if the caller
raised instead of committing.
"""
from types import TracebackType
from typing import Any, Optional

from social.infrastructure.db.pool import PostgresConnectionPool


class PostgresUnitOfWork:
    def __init__(self, pool: PostgresConnectionPool) -> None:
        self._pool = pool
        self._connection: Optional[Any] = None
        self._cursor: Optional[Any] = None

    @property
    def cursor(self) -> Any:
        if self._cursor is None:
            raise RuntimeError("UnitOfWork must be used as a context manager")
        return self._cursor

    def __enter__(self) -> "PostgresUnitOfWork":
        self._connection = self._pool.get_connection()
        self._cursor = self._connection.cursor()
        return self

    def commit(self) -> None:
        self._connection.commit()

    def rollback(self) -> None:
        self._connection.rollback()

    def __exit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc: Optional[BaseException],
        tb: Optional[TracebackType],
    ) -> None:
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
