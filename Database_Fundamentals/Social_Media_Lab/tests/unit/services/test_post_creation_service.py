"""Unit tests for PostService.create_post."""

from __future__ import annotations

from social_platform.features.posts.service import PostService
from tests.unit.services._fakes import (
    FakeActivityLogRepository,
    FakePostRepository,
    FakeTagRepository,
)


def test_create_post_stores_location_as_metadata_and_tags_as_relational_rows(
    fake_post_repository: FakePostRepository,
    fake_tag_repository: FakeTagRepository,
    fake_activity_log_repository: FakeActivityLogRepository,
) -> None:
    """Location is packed into the post's JSONB metadata; tags become attached rows."""
    service = PostService(fake_post_repository, fake_tag_repository, fake_activity_log_repository)

    post = service.create_post(1, "hello", tags=["python", "sql"], location="Kigali")

    assert post.metadata == {"location": "Kigali"}
    assert fake_tag_repository.get_tags_for_post(post.post_id) == ["python", "sql"]


def test_create_post_omits_metadata_keys_that_were_not_provided(
    fake_post_repository: FakePostRepository,
    fake_tag_repository: FakeTagRepository,
    fake_activity_log_repository: FakeActivityLogRepository,
) -> None:
    """A post created with no tags or location has empty metadata and no attached tags."""
    service = PostService(fake_post_repository, fake_tag_repository, fake_activity_log_repository)

    post = service.create_post(1, "hello")

    assert post.metadata == {}
    assert fake_tag_repository.get_tags_for_post(post.post_id) == []


def test_create_post_logs_a_post_created_activity_event(
    fake_post_repository: FakePostRepository,
    fake_tag_repository: FakeTagRepository,
    fake_activity_log_repository: FakeActivityLogRepository,
) -> None:
    """Creating a post logs exactly one post_created activity event."""
    service = PostService(fake_post_repository, fake_tag_repository, fake_activity_log_repository)

    post = service.create_post(1, "hello")

    assert len(fake_activity_log_repository.recorded_events) == 1
    assert fake_activity_log_repository.recorded_events[0].target_post_id == post.post_id


def test_create_post_succeeds_even_when_activity_logging_fails(
    fake_post_repository: FakePostRepository, fake_tag_repository: FakeTagRepository
) -> None:
    """A Mongo logging failure never undoes or fails an already-committed post."""
    failing_activity_log_repository = FakeActivityLogRepository(
        raise_on_record=RuntimeError("boom")
    )
    service = PostService(
        fake_post_repository, fake_tag_repository, failing_activity_log_repository
    )

    post = service.create_post(1, "hello")

    assert post.content == "hello"
