"""Data access for the comments table. No business logic, no commits."""
from typing import Any, Mapping, Sequence

import psycopg2

from social.exceptions import PostNotFoundError, UserNotFoundError
from social.models import Comment


class PostgresCommentRepository:
    def create(self, cursor: Any, comment: Comment) -> Comment:
        try:
            cursor.execute(
                """
                INSERT INTO comments (post_id, author_id, body)
                VALUES (%s, %s, %s)
                RETURNING id, post_id, author_id, body, created_at
                """,
                (comment.post_id, comment.author_id, comment.body),
            )
        except psycopg2.errors.ForeignKeyViolation as exc:
            constraint = exc.diag.constraint_name
            if constraint == "comments_post_id_fkey":
                raise PostNotFoundError(f"No post with id {comment.post_id}.") from exc
            raise UserNotFoundError(f"No user with id {comment.author_id}.") from exc
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

    def count_by_posts(self, cursor: Any, post_ids: Sequence[int]) -> Mapping[int, int]:
        """Comment count per post, in one round trip. Posts with zero
        comments are simply absent from the result - callers should default
        missing keys to 0."""
        if not post_ids:
            return {}
        cursor.execute(
            "SELECT post_id, COUNT(*) FROM comments WHERE post_id = ANY(%s) GROUP BY post_id",
            (list(post_ids),),
        )
        return dict(cursor.fetchall())


def _row_to_comment(row: Any) -> Comment:
    comment_id, post_id, author_id, body, created_at = row
    return Comment(
        id=comment_id,
        post_id=post_id,
        author_id=author_id,
        body=body,
        created_at=created_at,
    )
