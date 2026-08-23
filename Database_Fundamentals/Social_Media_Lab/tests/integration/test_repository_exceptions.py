"""Each of these confirms a real Postgres constraint violation - looked up
by the driver's `diag.constraint_name`, not by guessing from the error
message - comes back out of the repository as the matching domain
exception from `social.exceptions`, not a raw `psycopg2.errors.*` type.

Every test's constraint-violating call is its last database statement:
once Postgres aborts a transaction on a constraint violation, no further
statement can run on it, and the `cursor` fixture's rollback at teardown
doesn't care either way.
"""
import pytest

from social.exceptions import (
    AlreadyFollowingError,
    AlreadyLikedError,
    DuplicateEmailError,
    DuplicateUsernameError,
    PostNotFoundError,
    SelfFollowError,
    UserNotFoundError,
)
from social.models import Comment, Post, User
from social.repositories.comment_repository import PostgresCommentRepository
from social.repositories.follower_repository import PostgresFollowerRepository
from social.repositories.like_repository import PostgresLikeRepository
from social.repositories.post_repository import PostgresPostRepository
from social.repositories.user_repository import PostgresUserRepository


def _create_user(cursor, username, email):
    return PostgresUserRepository().create(
        cursor, User(id=None, username=username, email=email, password_hash="x")
    )


def _create_post(cursor, author_id, body="hello"):
    return PostgresPostRepository().create(
        cursor, Post(id=None, author_id=author_id, body=body)
    )


def test_duplicate_username_raises_duplicate_username_error(cursor):
    _create_user(cursor, "ada", "ada@example.com")

    with pytest.raises(DuplicateUsernameError):
        _create_user(cursor, "ada", "someone-else@example.com")


def test_duplicate_email_raises_duplicate_email_error(cursor):
    _create_user(cursor, "ada", "ada@example.com")

    with pytest.raises(DuplicateEmailError):
        _create_user(cursor, "someone-else", "ada@example.com")


def test_post_by_nonexistent_author_raises_user_not_found(cursor):
    with pytest.raises(UserNotFoundError):
        _create_post(cursor, author_id=999)


def test_follow_with_nonexistent_user_raises_user_not_found(cursor):
    with pytest.raises(UserNotFoundError):
        PostgresFollowerRepository().create(cursor, 999, 998)


def test_follow_self_raises_self_follow_error(cursor):
    ada = _create_user(cursor, "ada", "ada@example.com")

    with pytest.raises(SelfFollowError):
        PostgresFollowerRepository().create(cursor, ada.id, ada.id)


def test_duplicate_follow_raises_already_following_error(cursor):
    ada = _create_user(cursor, "ada", "ada@example.com")
    bob = _create_user(cursor, "bob", "bob@example.com")
    PostgresFollowerRepository().create(cursor, ada.id, bob.id)

    with pytest.raises(AlreadyFollowingError):
        PostgresFollowerRepository().create(cursor, ada.id, bob.id)


def test_like_nonexistent_post_raises_post_not_found(cursor):
    ada = _create_user(cursor, "ada", "ada@example.com")

    with pytest.raises(PostNotFoundError):
        PostgresLikeRepository().create(cursor, ada.id, 999)


def test_like_with_nonexistent_user_raises_user_not_found(cursor):
    post = _create_post(cursor, author_id=_create_user(cursor, "ada", "ada@example.com").id)

    with pytest.raises(UserNotFoundError):
        PostgresLikeRepository().create(cursor, 999, post.id)


def test_duplicate_like_raises_already_liked_error(cursor):
    ada = _create_user(cursor, "ada", "ada@example.com")
    post = _create_post(cursor, author_id=ada.id)
    PostgresLikeRepository().create(cursor, ada.id, post.id)

    with pytest.raises(AlreadyLikedError):
        PostgresLikeRepository().create(cursor, ada.id, post.id)


def test_comment_on_nonexistent_post_raises_post_not_found(cursor):
    ada = _create_user(cursor, "ada", "ada@example.com")

    with pytest.raises(PostNotFoundError):
        PostgresCommentRepository().create(
            cursor, Comment(id=None, post_id=999, author_id=ada.id, body="hi")
        )


def test_comment_by_nonexistent_author_raises_user_not_found(cursor):
    ada = _create_user(cursor, "ada", "ada@example.com")
    post = _create_post(cursor, author_id=ada.id)

    with pytest.raises(UserNotFoundError):
        PostgresCommentRepository().create(
            cursor, Comment(id=None, post_id=post.id, author_id=999, body="hi")
        )
