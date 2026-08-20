"""Unit tests for PostgresTagRepository: the get-or-create + attach-to-post flow."""

from __future__ import annotations

from unittest.mock import MagicMock

from social_platform.features.tags.repository import PostgresTagRepository


def test_attach_tags_does_nothing_for_an_empty_list(
    fake_connection_pool: MagicMock, fake_cursor: MagicMock
) -> None:
    """No tags means no queries at all -- not even an empty transaction."""
    repository = PostgresTagRepository(fake_connection_pool)

    repository.attach_tags(1, [])

    fake_cursor.execute.assert_not_called()


def test_attach_tags_upserts_each_tag_then_links_it_to_the_post(
    fake_connection_pool: MagicMock, fake_cursor: MagicMock
) -> None:
    """Each tag name is get-or-created, then linked to the post via the join table."""
    fake_cursor.fetchone.side_effect = [{"tag_id": 10}, {"tag_id": 20}]
    repository = PostgresTagRepository(fake_connection_pool)

    repository.attach_tags(1, ["python", "postgres"])

    all_params = [call_args.args[1] for call_args in fake_cursor.execute.call_args_list]
    assert all_params == [
        {"name": "python"},
        {"post_id": 1, "tag_id": 10},
        {"name": "postgres"},
        {"post_id": 1, "tag_id": 20},
    ]
    all_sql = [call_args.args[0] for call_args in fake_cursor.execute.call_args_list]
    assert "INSERT INTO tags" in all_sql[0]
    assert "INSERT INTO post_tags" in all_sql[1]


def test_get_tags_for_post_returns_the_names_from_the_join(
    fake_connection_pool: MagicMock, fake_cursor: MagicMock
) -> None:
    """Tag names come back from the tags/post_tags join, not raw ids."""
    fake_cursor.fetchall.return_value = [{"name": "postgres"}, {"name": "python"}]
    repository = PostgresTagRepository(fake_connection_pool)

    tags = repository.get_tags_for_post(1)

    assert tags == ["postgres", "python"]
