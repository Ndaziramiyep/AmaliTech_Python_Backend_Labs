"""Superseded: this test only verified the enum's own literal membership.

`FollowResult`/`UnfollowResult` now live in `social_platform.features.followers.model`,
and their behavior is exercised indirectly by `tests/unit/services/test_user_following_service.py`.
Delete this file (and the rest of this `tests/unit/models/` folder, which has no
replacement) whenever convenient -- it collects zero tests and is kept only because bulk
deletion was blocked during the restructure.
"""

from __future__ import annotations
