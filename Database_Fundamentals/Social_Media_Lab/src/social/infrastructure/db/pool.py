"""Thin wrapper around psycopg2's ThreadedConnectionPool."""
from psycopg2.extensions import connection as PgConnection
from psycopg2.pool import ThreadedConnectionPool


class PostgresConnectionPool:
    def __init__(self, dsn: str, min_size: int, max_size: int) -> None:
        self._pool = ThreadedConnectionPool(min_size, max_size, dsn)

    def get_connection(self) -> PgConnection:
        return self._pool.getconn()

    def release_connection(self, connection: PgConnection, *, discard: bool = False) -> None:
        self._pool.putconn(connection, close=discard)

    def close_all(self) -> None:
        self._pool.closeall()
