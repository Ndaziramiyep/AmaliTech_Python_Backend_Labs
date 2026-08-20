"""Unit tests for UserService.search_users."""

from __future__ import annotations

from social_platform.features.users.service import UserService
from tests.unit.services._fakes import FakeActivityLogRepository, FakeUserRepository


def test_search_users_finds_a_case_insensitive_substring_match(
    fake_user_repository: FakeUserRepository,
    fake_activity_log_repository: FakeActivityLogRepository,
) -> None:
    """A query matches usernames containing it, regardless of case."""
    fake_user_repository.create_user("Ada", "ada@example.com", "hash")
    fake_user_repository.create_user("grace", "grace@example.com", "hash")
    service = UserService(fake_user_repository, fake_activity_log_repository)

    results = service.search_users("AD")

    assert [user.username for user in results] == ["Ada"]


def test_search_users_returns_nothing_for_no_match(
    fake_user_repository: FakeUserRepository,
    fake_activity_log_repository: FakeActivityLogRepository,
) -> None:
    """A query matching no username returns an empty list, not an error."""
    fake_user_repository.create_user("ada", "ada@example.com", "hash")
    service = UserService(fake_user_repository, fake_activity_log_repository)

    assert service.search_users("nonexistent") == []
