"""Unit tests for PostService.create_post."""

from __future__ import annotations

from social_platform.features.posts.service import PostService
from tests.unit.services._fakes import FakeActivityLogRepository, FakePostRepository


def test_create_post_stores_tags_and_location_as_metadata(
    fake_post_repository: FakePostRepository,
    fake_activity_log_repository: FakeActivityLogRepository,
) -> None:
    """Tags and location are packed into the post's JSONB metadata dict."""
    service = PostService(fake_post_repository, fake_activity_log_repository)

    post = service.create_post(1, "hello", tags=["python", "sql"], location="Kigali")

    assert post.metadata == {"tags": ["python", "sql"], "location": "Kigali"}


def test_create_post_omits_metadata_keys_that_were_not_provided(
    fake_post_repository: FakePostRepository,
    fake_activity_log_repository: FakeActivityLogRepository,
) -> None:
    """A post created with no tags or location has empty metadata."""
    service = PostService(fake_post_repository, fake_activity_log_repository)

    post = service.create_post(1, "hello")

    assert post.metadata == {}


def test_create_post_logs_a_post_created_activity_event(
    fake_post_repository: FakePostRepository,
    fake_activity_log_repository: FakeActivityLogRepository,
) -> None:
    """Creating a post logs exactly one post_created activity event."""
    service = PostService(fake_post_repository, fake_activity_log_repository)

    post = service.create_post(1, "hello")

    assert len(fake_activity_log_repository.recorded_events) == 1
    assert fake_activity_log_repository.recorded_events[0].target_post_id == post.post_id


def test_create_post_succeeds_even_when_activity_logging_fails(
    fake_post_repository: FakePostRepository,
) -> None:
    """A Mongo logging failure never undoes or fails an already-committed post."""
    failing_activity_log_repository = FakeActivityLogRepository(
        raise_on_record=RuntimeError("boom")
    )
    service = PostService(fake_post_repository, failing_activity_log_repository)

    post = service.create_post(1, "hello")

    assert post.content == "hello"
