"""Unit tests for domain entity construction and equality."""

from __future__ import annotations

from datetime import datetime

from social_platform.models.entities import ActivityEvent, ActivityEventType, User


def test_two_users_with_the_same_fields_are_equal(sample_created_at: datetime) -> None:
    """User is a value object: equality is field-by-field, not identity."""
    first_user = User(1, "ada", "ada@example.com", "Ada Lovelace", sample_created_at)
    second_user = User(1, "ada", "ada@example.com", "Ada Lovelace", sample_created_at)

    assert first_user == second_user


def test_activity_event_defaults_target_fields_to_none(sample_created_at: datetime) -> None:
    """An activity event with no explicit target leaves target fields unset."""
    event = ActivityEvent(
        event_type=ActivityEventType.POST_LIKED,
        actor_user_id=1,
        occurred_at=sample_created_at,
    )

    assert event.target_user_id is None
    assert event.target_post_id is None
    assert event.details is None
