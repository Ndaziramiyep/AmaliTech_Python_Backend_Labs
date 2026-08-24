"""Thin wrapper around psycopg2's ThreadedConnectionPool."""
from psycopg2.extensions import connection as PgConnection
from psycopg2.pool import ThreadedConnectionPool


class PostgresConnectionPool:
    """Wraps a psycopg2 ThreadedConnectionPool for acquiring and releasing connections."""

    def __init__(self, dsn: str, min_size: int, max_size: int) -> None:
        """Create the underlying threaded connection pool for the given DSN and size bounds."""
        self._pool = ThreadedConnectionPool(min_size, max_size, dsn)

    def get_connection(self) -> PgConnection:
        """Acquire and return a connection from the pool."""
        return self._pool.getconn()

    def release_connection(self, connection: PgConnection, *, discard: bool = False) -> None:
        """Return a connection to the pool, discarding it instead of reusing it if requested."""
        self._pool.putconn(connection, close=discard)

    def close_all(self) -> None:
        """Close every connection in the pool."""
        self._pool.closeall()
