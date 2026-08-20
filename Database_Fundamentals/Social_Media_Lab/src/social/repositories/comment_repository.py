"""Data access for the comments table. No business logic, no commits."""
from typing import Any, Sequence

from social.domain.models import Comment


class PostgresCommentRepository:
    def create(self, cursor: Any, comment: Comment) -> Comment:
        cursor.execute(
            """
            INSERT INTO comments (post_id, author_id, body)
            VALUES (%s, %s, %s)
            RETURNING id, post_id, author_id, body, created_at
            """,
            (comment.post_id, comment.author_id, comment.body),
        )
        return _row_to_comment(cursor.fetchone())

    def list_by_post(self, cursor: Any, post_id: int) -> Sequence[Comment]:
        cursor.execute(
            """
            SELECT id, post_id, author_id, body, created_at
            FROM comments
            WHERE post_id = %s
            ORDER BY created_at ASC
            """,
            (post_id,),
        )
        return [_row_to_comment(row) for row in cursor.fetchall()]


def _row_to_comment(row: Any) -> Comment:
    comment_id, post_id, author_id, body, created_at = row
    return Comment(
        id=comment_id,
        post_id=post_id,
        author_id=author_id,
        body=body,
        created_at=created_at,
    )
