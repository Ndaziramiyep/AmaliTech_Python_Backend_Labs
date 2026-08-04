"""Unit tests for the FollowResult/UnfollowResult outcome enums."""

from __future__ import annotations

from social_platform.models.results import FollowResult, UnfollowResult


def test_follow_result_has_exactly_two_members() -> None:
    """FollowResult models exactly the created/already-exists outcomes."""
    assert {member.value for member in FollowResult} == {"created", "already_exists"}


def test_unfollow_result_has_exactly_two_members() -> None:
    """UnfollowResult models exactly the removed/did-not-exist outcomes."""
    assert {member.value for member in UnfollowResult} == {"removed", "did_not_exist"}
