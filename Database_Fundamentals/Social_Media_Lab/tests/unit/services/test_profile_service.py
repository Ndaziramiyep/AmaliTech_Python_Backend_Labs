"""Unit tests for ProfileService.get_profile."""

from __future__ import annotations

import pytest

from social_platform.common.exceptions import UserNotFoundError
from social_platform.features.profile.service import ProfileService
from tests.unit.services._fakes import (
    FakeFollowerRepository,
    FakePostRepository,
    FakeUserRepository,
)


def test_get_profile_raises_when_the_username_does_not_exist(
    fake_user_repository: FakeUserRepository,
    fake_post_repository: FakePostRepository,
    fake_follower_repository: FakeFollowerRepository,
) -> None:
    """Looking up a nonexistent username raises UserNotFoundError, not a silent default."""
    service = ProfileService(fake_user_repository, fake_post_repository, fake_follower_repository)

    with pytest.raises(UserNotFoundError):
        service.get_profile("nobody")


def test_get_profile_composes_bio_and_counts_from_three_repositories(
    fake_user_repository: FakeUserRepository,
    fake_post_repository: FakePostRepository,
    fake_follower_repository: FakeFollowerRepository,
) -> None:
    """The profile combines the user's bio with post/follower/following counts."""
    user = fake_user_repository.create_user("ada", "ada@example.com", "hash", "Mathematician.")
    fake_post_repository.create_post(user.user_id, "hello", {})
    fake_post_repository.create_post(user.user_id, "world", {})
    fake_follower_repository.follower_count_to_return = 3
    fake_follower_repository.following_count_to_return = 5
    service = ProfileService(fake_user_repository, fake_post_repository, fake_follower_repository)

    profile = service.get_profile("ada")

    assert profile.username == "ada"
    assert profile.bio == "Mathematician."
    assert profile.post_count == 2
    assert profile.follower_count == 3
    assert profile.following_count == 5
