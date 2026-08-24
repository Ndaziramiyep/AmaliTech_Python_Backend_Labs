"""Each test confirms that a real Postgres constraint violation, identified via the driver's `diag.constraint_name` rather than guessed from the error message, surfaces from the repository as the matching domain exception rather than a raw `psycopg2.errors.*` type, and is always the test's last database statement since Postgres aborts the transaction once that violation occurs."""
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
    """Create and return a user with the given username and email."""
    return PostgresUserRepository().create(
        cursor, User(id=None, username=username, email=email, password_hash="x")
    )


def _create_post(cursor, author_id, body="hello"):
    """Create and return a post by the given author."""
    return PostgresPostRepository().create(
        cursor, Post(id=None, author_id=author_id, body=body)
    )


def test_duplicate_username_raises_duplicate_username_error(cursor):
    """Test that creating a user with an already-used username raises DuplicateUsernameError."""
    _create_user(cursor, "ada", "ada@example.com")

    with pytest.raises(DuplicateUsernameError):
        _create_user(cursor, "ada", "someone-else@example.com")


def test_duplicate_email_raises_duplicate_email_error(cursor):
    """Test that creating a user with an already-used email raises DuplicateEmailError."""
    _create_user(cursor, "ada", "ada@example.com")

    with pytest.raises(DuplicateEmailError):
        _create_user(cursor, "someone-else", "ada@example.com")


def test_post_by_nonexistent_author_raises_user_not_found(cursor):
    """Test that creating a post for a nonexistent author raises UserNotFoundError."""
    with pytest.raises(UserNotFoundError):
        _create_post(cursor, author_id=999)


def test_follow_with_nonexistent_user_raises_user_not_found(cursor):
    """Test that following with a nonexistent user id raises UserNotFoundError."""
    with pytest.raises(UserNotFoundError):
        PostgresFollowerRepository().create(cursor, 999, 998)


def test_follow_self_raises_self_follow_error(cursor):
    """Test that a user following themselves raises SelfFollowError."""
    ada = _create_user(cursor, "ada", "ada@example.com")

    with pytest.raises(SelfFollowError):
        PostgresFollowerRepository().create(cursor, ada.id, ada.id)


def test_duplicate_follow_raises_already_following_error(cursor):
    """Test that following the same user twice raises AlreadyFollowingError."""
    ada = _create_user(cursor, "ada", "ada@example.com")
    bob = _create_user(cursor, "bob", "bob@example.com")
    PostgresFollowerRepository().create(cursor, ada.id, bob.id)

    with pytest.raises(AlreadyFollowingError):
        PostgresFollowerRepository().create(cursor, ada.id, bob.id)


def test_like_nonexistent_post_raises_post_not_found(cursor):
    """Test that liking a nonexistent post raises PostNotFoundError."""
    ada = _create_user(cursor, "ada", "ada@example.com")

    with pytest.raises(PostNotFoundError):
        PostgresLikeRepository().create(cursor, ada.id, 999)


def test_like_with_nonexistent_user_raises_user_not_found(cursor):
    """Test that liking a post with a nonexistent user id raises UserNotFoundError."""
    post = _create_post(cursor, author_id=_create_user(cursor, "ada", "ada@example.com").id)

    with pytest.raises(UserNotFoundError):
        PostgresLikeRepository().create(cursor, 999, post.id)


def test_duplicate_like_raises_already_liked_error(cursor):
    """Test that liking the same post twice raises AlreadyLikedError."""
    ada = _create_user(cursor, "ada", "ada@example.com")
    post = _create_post(cursor, author_id=ada.id)
    PostgresLikeRepository().create(cursor, ada.id, post.id)

    with pytest.raises(AlreadyLikedError):
        PostgresLikeRepository().create(cursor, ada.id, post.id)


def test_comment_on_nonexistent_post_raises_post_not_found(cursor):
    """Test that commenting on a nonexistent post raises PostNotFoundError."""
    ada = _create_user(cursor, "ada", "ada@example.com")

    with pytest.raises(PostNotFoundError):
        PostgresCommentRepository().create(
            cursor, Comment(id=None, post_id=999, author_id=ada.id, body="hi")
        )


def test_comment_by_nonexistent_author_raises_user_not_found(cursor):
    """Test that commenting with a nonexistent author id raises UserNotFoundError."""
    ada = _create_user(cursor, "ada", "ada@example.com")
    post = _create_post(cursor, author_id=ada.id)

    with pytest.raises(UserNotFoundError):
        PostgresCommentRepository().create(
            cursor, Comment(id=None, post_id=post.id, author_id=999, body="hi")
        )
