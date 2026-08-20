import pytest

from social.services.post_service import PostService

from .fakes import FakeActivityLogger, FakePostRepository, FakeUnitOfWork


class PostInsertFailure(Exception):
    """Stand-in for any Postgres error on the posts INSERT (e.g. bad FK)."""


def test_create_post_commits_once_then_logs_activity_with_jsonb_metadata():
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
    repository = FakePostRepository()
    uow = FakeUnitOfWork()
    logger = FakeActivityLogger()
    service = PostService(lambda: uow, repository, logger)

    result = service.create_post(author_id=1, body="hello")

    assert result.metadata == {}


def test_create_post_rolls_back_and_leaves_no_side_effects_when_insert_fails():
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
