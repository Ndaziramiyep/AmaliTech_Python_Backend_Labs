"""Unit tests for PostService.update_post, delete_post, and get_posts_by_author."""

from __future__ import annotations

import pytest

from social_platform.common.exceptions import OwnershipError, PostNotFoundError
from social_platform.features.posts.service import PostService
from tests.unit.services._fakes import (
    FakeActivityLogRepository,
    FakePostRepository,
    FakeTagRepository,
)


def test_update_post_rejects_a_non_owner(
    fake_post_repository: FakePostRepository,
    fake_tag_repository: FakeTagRepository,
    fake_activity_log_repository: FakeActivityLogRepository,
) -> None:
    """Updating someone else's post raises OwnershipError, never silently succeeds."""
    post = fake_post_repository.create_post(1, "hello", {})
    service = PostService(fake_post_repository, fake_tag_repository, fake_activity_log_repository)

    with pytest.raises(OwnershipError):
        service.update_post(post.post_id, 999, "hijacked content")


def test_update_post_rejects_a_nonexistent_post(
    fake_post_repository: FakePostRepository,
    fake_tag_repository: FakeTagRepository,
    fake_activity_log_repository: FakeActivityLogRepository,
) -> None:
    """Updating a post that doesn't exist raises PostNotFoundError."""
    service = PostService(fake_post_repository, fake_tag_repository, fake_activity_log_repository)

    with pytest.raises(PostNotFoundError):
        service.update_post(999, 1, "new content")


def test_update_post_by_the_owner_replaces_content_and_location(
    fake_post_repository: FakePostRepository,
    fake_tag_repository: FakeTagRepository,
    fake_activity_log_repository: FakeActivityLogRepository,
) -> None:
    """The author can update their own post's content and location."""
    post = fake_post_repository.create_post(1, "hello", {})
    service = PostService(fake_post_repository, fake_tag_repository, fake_activity_log_repository)

    updated_post = service.update_post(post.post_id, 1, "updated content", "Kigali")

    assert updated_post.content == "updated content"
    assert updated_post.metadata == {"location": "Kigali"}


def test_delete_post_rejects_a_non_owner(
    fake_post_repository: FakePostRepository,
    fake_tag_repository: FakeTagRepository,
    fake_activity_log_repository: FakeActivityLogRepository,
) -> None:
    """Deleting someone else's post raises OwnershipError, and the post survives."""
    post = fake_post_repository.create_post(1, "hello", {})
    service = PostService(fake_post_repository, fake_tag_repository, fake_activity_log_repository)

    with pytest.raises(OwnershipError):
        service.delete_post(post.post_id, 999)
    assert fake_post_repository.find_post_by_id(post.post_id) is not None


def test_delete_post_by_the_owner_removes_it(
    fake_post_repository: FakePostRepository,
    fake_tag_repository: FakeTagRepository,
    fake_activity_log_repository: FakeActivityLogRepository,
) -> None:
    """The author can delete their own post."""
    post = fake_post_repository.create_post(1, "hello", {})
    service = PostService(fake_post_repository, fake_tag_repository, fake_activity_log_repository)

    service.delete_post(post.post_id, 1)

    assert fake_post_repository.find_post_by_id(post.post_id) is None


def test_get_posts_by_author_returns_only_that_authors_posts(
    fake_post_repository: FakePostRepository,
    fake_tag_repository: FakeTagRepository,
    fake_activity_log_repository: FakeActivityLogRepository,
) -> None:
    """Another author's posts never appear in the results."""
    fake_post_repository.create_post(1, "mine", {})
    fake_post_repository.create_post(2, "not mine", {})
    service = PostService(fake_post_repository, fake_tag_repository, fake_activity_log_repository)

    posts = service.get_posts_by_author(1)

    assert [post.content for post in posts] == ["mine"]
