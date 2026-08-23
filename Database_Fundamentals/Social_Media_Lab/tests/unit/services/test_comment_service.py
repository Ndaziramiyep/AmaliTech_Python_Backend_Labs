import pytest

from social.services.comment_service import CommentService

from .fakes import FakeActivityLogger, FakeCommentRepository, FakeUnitOfWork


class CommentInsertFailure(Exception):
    """Stand-in for any Postgres error on the comments INSERT (e.g. bad FK)."""


def test_create_comment_commits_once_then_logs_activity():
    repository = FakeCommentRepository()
    uow = FakeUnitOfWork()
    logger = FakeActivityLogger()
    service = CommentService(lambda: uow, repository, logger)

    result = service.create_comment(post_id=1, author_id=2, body="nice post")

    assert result.id == 1
    assert result.post_id == 1
    assert result.author_id == 2
    assert result.body == "nice post"
    assert repository.received_cursor is uow.cursor
    assert uow.committed is True
    assert uow.rolled_back is False
    assert logger.entries == [("comment_created", {"comment_id": 1, "post_id": 1, "author_id": 2})]


def test_create_comment_rolls_back_and_leaves_no_side_effects_when_insert_fails():
    error = CommentInsertFailure("post_id fk violation")
    repository = FakeCommentRepository(raise_error=error)
    uow = FakeUnitOfWork()
    logger = FakeActivityLogger()
    service = CommentService(lambda: uow, repository, logger)

    with pytest.raises(CommentInsertFailure):
        service.create_comment(post_id=999, author_id=2, body="nice post")

    assert uow.committed is False
    assert uow.rolled_back is True
    assert logger.entries == []


def test_list_comments_returns_comments_for_that_post():
    repository = FakeCommentRepository()
    uow = FakeUnitOfWork()
    logger = FakeActivityLogger()
    service = CommentService(lambda: uow, repository, logger)
    service.create_comment(post_id=1, author_id=2, body="first")
    service.create_comment(post_id=2, author_id=3, body="unrelated")

    result = service.list_comments(post_id=1)

    assert [c.body for c in result] == ["first"]


def test_count_by_posts_returns_per_post_comment_counts():
    repository = FakeCommentRepository()
    uow = FakeUnitOfWork()
    logger = FakeActivityLogger()
    service = CommentService(lambda: uow, repository, logger)
    service.create_comment(post_id=1, author_id=2, body="first")
    service.create_comment(post_id=1, author_id=3, body="second")
    service.create_comment(post_id=2, author_id=3, body="unrelated")

    result = service.count_by_posts([1, 2, 3])

    assert result == {1: 2, 2: 1}
    assert 3 not in result
