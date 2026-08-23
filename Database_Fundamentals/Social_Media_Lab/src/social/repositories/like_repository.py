"""Data access for the likes table. No business logic, no commits."""
from typing import Any, Mapping, Sequence

from social.models import Like


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

    def count_by_posts(self, cursor: Any, post_ids: Sequence[int]) -> Mapping[int, int]:
        """Like count per post, in one round trip. Posts with zero likes are
        simply absent from the result - callers should default missing keys
        to 0."""
        if not post_ids:
            return {}
        cursor.execute(
            "SELECT post_id, COUNT(*) FROM likes WHERE post_id = ANY(%s) GROUP BY post_id",
            (list(post_ids),),
        )
        return dict(cursor.fetchall())
