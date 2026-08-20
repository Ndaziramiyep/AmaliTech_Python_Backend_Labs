"""Tag persistence: the `TagRepository` contract and its PostgreSQL implementation.

Tags are a many-to-many relationship (`tags` <-> `post_tags` <-> `posts`), not a JSONB
array, so "how many posts use this tag" and "which posts have this tag" are ordinary
indexed joins instead of scanning every post's metadata.
"""

from __future__ import annotations

from typing import Protocol

from social_platform.common.postgres_pool import PostgresConnectionPool


class TagRepository(Protocol):
    """Persistence contract for tags. Services depend on this, not on Postgres."""

    def attach_tags(self, post_id: int, tag_names: list[str]) -> None:
        """Get-or-create each named tag and attach it to `post_id`."""

    def get_tags_for_post(self, post_id: int) -> list[str]:
        """Return the names of every tag attached to `post_id`, alphabetically."""


class PostgresTagRepository:
    """Implements `TagRepository` against PostgreSQL via a pooled connection."""

    def __init__(self, connection_pool: PostgresConnectionPool) -> None:
        self._connection_pool = connection_pool

    def attach_tags(self, post_id: int, tag_names: list[str]) -> None:
        """Get-or-create each named tag and attach it to `post_id`, in one transaction."""
        if not tag_names:
            return
        with self._connection_pool.cursor() as cursor:
            for tag_name in tag_names:
                cursor.execute(
                    """
                    INSERT INTO tags (name)
                    VALUES (%(name)s)
                    -- A no-op update (instead of DO NOTHING) so RETURNING still yields the
                    -- existing row's id when the tag already exists -- the standard
                    -- get-or-create-and-return-id idiom in PostgreSQL.
                    ON CONFLICT (name) DO UPDATE SET name = EXCLUDED.name
                    RETURNING tag_id
                    """,
                    {"name": tag_name},
                )
                row = cursor.fetchone()
                assert row is not None  # RETURNING always yields a row on upsert
                cursor.execute(
                    """
                    INSERT INTO post_tags (post_id, tag_id)
                    VALUES (%(post_id)s, %(tag_id)s)
                    ON CONFLICT (post_id, tag_id) DO NOTHING
                    """,
                    {"post_id": post_id, "tag_id": row["tag_id"]},
                )

    def get_tags_for_post(self, post_id: int) -> list[str]:
        """Return the names of every tag attached to `post_id`, alphabetically."""
        with self._connection_pool.cursor() as cursor:
            cursor.execute(
                """
                SELECT tags.name
                FROM tags
                JOIN post_tags ON post_tags.tag_id = tags.tag_id
                WHERE post_tags.post_id = %(post_id)s
                ORDER BY tags.name
                """,
                {"post_id": post_id},
            )
            rows = cursor.fetchall()
        return [row["name"] for row in rows]
