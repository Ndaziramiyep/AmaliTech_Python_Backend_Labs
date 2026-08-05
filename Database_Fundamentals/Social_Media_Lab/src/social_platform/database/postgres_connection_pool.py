"""Pooled PostgreSQL connection management with a transactional cursor context manager."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

import psycopg2
import psycopg2.pool
from psycopg2.extras import RealDictCursor

from social_platform.config.application_settings import PostgresSettings
from social_platform.models.exceptions import ConnectionPoolExhaustedError


class PostgresConnectionPool:
    """Owns a psycopg2 connection pool and the commit/rollback contract for its cursors."""

    def __init__(self, settings: PostgresSettings) -> None:
        self._pool = psycopg2.pool.ThreadedConnectionPool(
            settings.pool_min_size,
            settings.pool_max_size,
            host=settings.host,
            port=settings.port,
            dbname=settings.database_name,
            user=settings.username,
            password=settings.password,
        )

    @contextmanager
    def cursor(self) -> Iterator[RealDictCursor]:
        """Yield a cursor inside one transaction: commits on success, rolls back on error."""
        try:
            connection = self._pool.getconn()
        except psycopg2.pool.PoolError as pool_error:
            raise ConnectionPoolExhaustedError(
                "No PostgreSQL connection is available from the pool."
            ) from pool_error

        try:
            with connection:
                with connection.cursor(cursor_factory=RealDictCursor) as cursor:
                    yield cursor
        finally:
            self._pool.putconn(connection)

    def close_all_connections(self) -> None:
        """Close every connection currently held by the pool."""
        self._pool.closeall()
