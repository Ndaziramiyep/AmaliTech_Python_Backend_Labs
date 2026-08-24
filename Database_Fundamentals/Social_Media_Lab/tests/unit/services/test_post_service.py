"""Unit tests for PostService against fake repository, unit-of-work, and activity-logger collaborators."""
import pytest

from social.services.post_service import PostService

from .fakes import FakeActivityLogger, FakePostRepository, FakeUnitOfWork


class PostInsertFailure(Exception):
    """Stand-in for any Postgres error on the posts INSERT (e.g. bad FK)."""


def test_create_post_commits_once_then_logs_activity_with_jsonb_metadata():
    """Test that creating a post with metadata commits exactly once and then logs a post_created activity event."""
    repository = FakePostRepository()
    uow = FakeUnitOfWork()
    logger = FakeActivityLogger()
    service = PostService(lambda: uow, repository, logger)

    result = service.create_post(author_id=1, body="hello", metadata={"tags": ["intro"]})

    assert result.id == 1
    assert result.author_id == 1
    assert result.body == "hello"
    assert result.metadata == {"tags": ["intro"]}
    assert repository.received_cursor is uow.cursor
    assert uow.committed is True
    assert uow.rolled_back is False
    assert logger.entries == [("post_created", {"post_id": 1, "author_id": 1})]


def test_create_post_defaults_metadata_to_empty_dict():
    """Test that creating a post without metadata defaults its metadata to an empty dict."""
    repository = FakePostRepository()
    uow = FakeUnitOfWork()
    logger = FakeActivityLogger()
    service = PostService(lambda: uow, repository, logger)

    result = service.create_post(author_id=1, body="hello")

    assert result.metadata == {}


def test_create_post_rolls_back_and_leaves_no_side_effects_when_insert_fails():
    """Test that a failed post insert rolls back the transaction and logs no activity."""
    error = PostInsertFailure("author_id fk violation")
    repository = FakePostRepository(raise_error=error)
    uow = FakeUnitOfWork()
    logger = FakeActivityLogger()
    service = PostService(lambda: uow, repository, logger)

    with pytest.raises(PostInsertFailure):
        service.create_post(author_id=999, body="hello")

    assert uow.committed is False
    assert uow.rolled_back is True
    assert logger.entries == []


def test_list_recent_returns_newest_first():
    """Test that list_recent returns posts ordered from newest to oldest."""
    repository = FakePostRepository()
    uow = FakeUnitOfWork()
    logger = FakeActivityLogger()
    service = PostService(lambda: uow, repository, logger)
    service.create_post(author_id=1, body="first")
    service.create_post(author_id=1, body="second")

    result = service.list_recent()

    assert [p.body for p in result] == ["second", "first"]


def test_list_recent_respects_limit():
    """Test that list_recent returns no more posts than the given limit."""
    repository = FakePostRepository()
    uow = FakeUnitOfWork()
    logger = FakeActivityLogger()
    service = PostService(lambda: uow, repository, logger)
    for i in range(5):
        service.create_post(author_id=1, body=f"post {i}")

    result = service.list_recent(limit=2)

    assert len(result) == 2
