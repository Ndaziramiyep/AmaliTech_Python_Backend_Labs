"""The profile use case: composing a user's public info and activity counts on read."""

from __future__ import annotations

from social_platform.common.exceptions import UserNotFoundError
from social_platform.features.followers.repository import FollowerRepository
from social_platform.features.posts.repository import PostRepository
from social_platform.features.profile.model import UserProfile
from social_platform.features.users.repository import UserRepository


class ProfileService:
    """Builds a user's public profile by composing the users/posts/followers features."""

    def __init__(
        self,
        user_repository: UserRepository,
        post_repository: PostRepository,
        follower_repository: FollowerRepository,
    ) -> None:
        self._user_repository = user_repository
        self._post_repository = post_repository
        self._follower_repository = follower_repository

    def get_profile(self, username: str) -> UserProfile:
        """Return `username`'s public profile, or raise UserNotFoundError if no such user."""
        user = self._user_repository.find_user_by_username(username)
        if user is None:
            raise UserNotFoundError(f"No user with username {username!r} exists.")

        return UserProfile(
            user_id=user.user_id,
            username=user.username,
            bio=user.bio,
            post_count=self._post_repository.count_posts_by_author(user.user_id),
            follower_count=self._follower_repository.count_followers(user.user_id),
            following_count=self._follower_repository.count_following(user.user_id),
        )
