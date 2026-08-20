"""Data access for the followers table. No business logic, no commits."""
from typing import Any

from social.domain.models import Follower


class PostgresFollowerRepository:
    def create(self, cursor: Any, follower_id: int, followee_id: int) -> Follower:
        cursor.execute(
            """
            INSERT INTO followers (follower_id, followee_id)
            VALUES (%s, %s)
            RETURNING follower_id, followee_id, created_at
            """,
            (follower_id, followee_id),
        )
        row = cursor.fetchone()
        return Follower(follower_id=row[0], followee_id=row[1], created_at=row[2])

    def exists(self, cursor: Any, follower_id: int, followee_id: int) -> bool:
        cursor.execute(
            "SELECT 1 FROM followers WHERE follower_id = %s AND followee_id = %s",
            (follower_id, followee_id),
        )
        return cursor.fetchone() is not None
