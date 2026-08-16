"""Unit tests for PostgresFeedRepository: the CTE + ROW_NUMBER() timeline feed query."""

from __future__ import annotations

from datetime import datetime
from unittest.mock import MagicMock

from social_platform.features.feed.repository import PostgresFeedRepository


def test_fetch_feed_page_maps_every_row_and_passes_pagination_bounds(
    fake_connection_pool: MagicMock, fake_cursor: MagicMock, sample_created_at: datetime
) -> None:
    """Each row from the feed query becomes one FeedPostEntry, and bounds are parameterized."""
    fake_cursor.fetchall.return_value = [
        {
            "post_id": 1,
            "author_user_id": 2,
            "author_username": "ada",
            "content": "hello",
            "metadata": {},
            "created_at": sample_created_at,
        }
    ]
    repository = PostgresFeedRepository(fake_connection_pool)

    feed_page = repository.fetch_feed_page(1, 1, 20)

    assert len(feed_page) == 1
    assert feed_page[0].author_username == "ada"
    executed_params = fake_cursor.execute.call_args.args[1]
    assert executed_params == {"follower_user_id": 1, "first_row": 1, "last_row": 20}
