"""Data access for the likes table. No business logic, no commits."""
from typing import Any

from social.domain.models import Like


class PostgresLikeRepository:
    def create(self, cursor: Any, user_id: int, post_id: int) -> Like:
        cursor.execute(
            """
            INSERT INTO likes (user_id, post_id)
            VALUES (%s, %s)
            RETURNING user_id, post_id, created_at
            """,
            (user_id, post_id),
        )
        row = cursor.fetchone()
        return Like(user_id=row[0], post_id=row[1], created_at=row[2])

    def exists(self, cursor: Any, user_id: int, post_id: int) -> bool:
        cursor.execute(
            "SELECT 1 FROM likes WHERE user_id = %s AND post_id = %s",
            (user_id, post_id),
        )
        return cursor.fetchone() is not None
