"""Unit tests for UserService.update_bio."""

from __future__ import annotations

import pytest

from social_platform.common.exceptions import InvalidBioError
from social_platform.features.users.service import UserService
from tests.unit.services._fakes import FakeActivityLogRepository, FakeUserRepository


def test_update_bio_replaces_the_stored_bio(
    fake_user_repository: FakeUserRepository,
    fake_activity_log_repository: FakeActivityLogRepository,
) -> None:
    """A successful bio update is reflected on the returned user."""
    user = fake_user_repository.create_user("ada", "ada@example.com", "hash")
    service = UserService(fake_user_repository, fake_activity_log_repository)

    updated_user = service.update_bio(user.user_id, "Mathematician and computer scientist.")

    assert updated_user.bio == "Mathematician and computer scientist."


def test_update_bio_logs_a_bio_updated_activity_event(
    fake_user_repository: FakeUserRepository,
    fake_activity_log_repository: FakeActivityLogRepository,
) -> None:
    """Updating a bio logs exactly one bio_updated activity event."""
    user = fake_user_repository.create_user("ada", "ada@example.com", "hash")
    service = UserService(fake_user_repository, fake_activity_log_repository)

    service.update_bio(user.user_id, "New bio.")

    assert len(fake_activity_log_repository.recorded_events) == 1
    assert fake_activity_log_repository.recorded_events[0].actor_user_id == user.user_id


def test_update_bio_with_an_empty_string_clears_it(
    fake_user_repository: FakeUserRepository,
    fake_activity_log_repository: FakeActivityLogRepository,
) -> None:
    """Passing an empty bio clears it to None rather than storing an empty string."""
    user = fake_user_repository.create_user("ada", "ada@example.com", "hash", "Old bio.")
    service = UserService(fake_user_repository, fake_activity_log_repository)

    updated_user = service.update_bio(user.user_id, "")

    assert updated_user.bio is None


def test_update_bio_rejects_a_bio_that_is_too_long(
    fake_user_repository: FakeUserRepository,
    fake_activity_log_repository: FakeActivityLogRepository,
) -> None:
    """A bio over the length limit is rejected without touching the repository."""
    user = fake_user_repository.create_user("ada", "ada@example.com", "hash")
    service = UserService(fake_user_repository, fake_activity_log_repository)

    with pytest.raises(InvalidBioError):
        service.update_bio(user.user_id, "x" * 281)

    assert fake_user_repository.users_by_id[user.user_id].bio is None


def test_update_bio_succeeds_even_when_activity_logging_fails(
    fake_user_repository: FakeUserRepository,
) -> None:
    """A Mongo logging failure never undoes or fails an already-committed bio update."""
    user = fake_user_repository.create_user("ada", "ada@example.com", "hash")
    failing_activity_log_repository = FakeActivityLogRepository(
        raise_on_record=RuntimeError("boom")
    )
    service = UserService(fake_user_repository, failing_activity_log_repository)

    updated_user = service.update_bio(user.user_id, "New bio.")

    assert updated_user.bio == "New bio."
