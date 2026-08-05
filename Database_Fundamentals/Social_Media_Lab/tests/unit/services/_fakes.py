"""Hand-written fakes of the repository interfaces, used to unit test services without I/O."""

from __future__ import annotations

from datetime import datetime

from social_platform.models.entities import (
    ActivityEvent,
    Comment,
    FeedPostEntry,
    Post,
    PostMetadata,
    TrendingPostEntry,
    User,
)
from social_platform.models.results import FollowResult, UnfollowResult
from social_platform.repositories.interfaces import (
    ActivityLogRepositoryInterface,
    CommentRepositoryInterface,
    FollowerRepositoryInterface,
    PostRepositoryInterface,
    TimelineCacheRepositoryInterface,
    UserRepositoryInterface,
)


class FakeUserRepository(UserRepositoryInterface):
    """An in-memory stand-in for `UserRepositoryInterface`."""

    def __init__(self) -> None:
        self.users_by_id: dict[int, User] = {}
        self.password_hashes_by_username: dict[str, str] = {}
        self.next_user_id = 1

    def create_user(self, username: str, email: str, password_hash: str, display_name: str) -> User:
        user = User(self.next_user_id, username, email, display_name, datetime.now())
        self.users_by_id[user.user_id] = user
        self.password_hashes_by_username[username] = password_hash
        self.next_user_id += 1
        return user

    def find_user_by_id(self, user_id: int) -> User | None:
        return self.users_by_id.get(user_id)

    def find_user_and_password_hash_by_username(self, username: str) -> tuple[User, str] | None:
        password_hash = self.password_hashes_by_username.get(username)
        if password_hash is None:
            return None
        user = next(user for user in self.users_by_id.values() if user.username == username)
        return user, password_hash


class FakePostRepository(PostRepositoryInterface):
    """An in-memory stand-in for `PostRepositoryInterface`."""

    def __init__(self) -> None:
        self.posts_by_id: dict[int, Post] = {}
        self.next_post_id = 1
        self.feed_page_calls: list[tuple[int, int, int]] = []
        self.feed_page_to_return: list[FeedPostEntry] = []
        self.trending_posts_to_return: list[TrendingPostEntry] = []

    def create_post(self, author_user_id: int, content: str, metadata: PostMetadata) -> Post:
        post = Post(self.next_post_id, author_user_id, content, metadata, datetime.now())
        self.posts_by_id[post.post_id] = post
        self.next_post_id += 1
        return post

    def find_post_by_id(self, post_id: int) -> Post | None:
        return self.posts_by_id.get(post_id)

    def fetch_timeline_feed_page(
        self, follower_user_id: int, first_row: int, last_row: int
    ) -> list[FeedPostEntry]:
        self.feed_page_calls.append((follower_user_id, first_row, last_row))
        return self.feed_page_to_return

    def fetch_trending_posts(self, since: datetime, result_limit: int) -> list[TrendingPostEntry]:
        return self.trending_posts_to_return


class FakeCommentRepository(CommentRepositoryInterface):
    """An in-memory stand-in for `CommentRepositoryInterface`."""

    def __init__(self) -> None:
        self.next_comment_id = 1

    def create_comment(self, post_id: int, commenter_user_id: int, content: str) -> Comment:
        comment = Comment(self.next_comment_id, post_id, commenter_user_id, content, datetime.now())
        self.next_comment_id += 1
        return comment


class FakeFollowerRepository(FollowerRepositoryInterface):
    """An in-memory stand-in for `FollowerRepositoryInterface`."""

    def __init__(self) -> None:
        self.follow_result_to_return = FollowResult.CREATED
        self.unfollow_result_to_return = UnfollowResult.REMOVED
        self.create_calls: list[tuple[int, int]] = []
        self.delete_calls: list[tuple[int, int]] = []

    def create_follow_relationship(
        self, follower_user_id: int, followee_user_id: int
    ) -> FollowResult:
        self.create_calls.append((follower_user_id, followee_user_id))
        return self.follow_result_to_return

    def delete_follow_relationship(
        self, follower_user_id: int, followee_user_id: int
    ) -> UnfollowResult:
        self.delete_calls.append((follower_user_id, followee_user_id))
        return self.unfollow_result_to_return


class FakeTimelineCacheRepository(TimelineCacheRepositoryInterface):
    """An in-memory stand-in for `TimelineCacheRepositoryInterface`."""

    def __init__(self) -> None:
        self.cached_pages: dict[tuple[int, int], list[FeedPostEntry]] = {}

    def get_cached_feed_page(
        self, follower_user_id: int, page_number: int
    ) -> list[FeedPostEntry] | None:
        return self.cached_pages.get((follower_user_id, page_number))

    def set_cached_feed_page(
        self, follower_user_id: int, page_number: int, feed_page: list[FeedPostEntry]
    ) -> None:
        self.cached_pages[(follower_user_id, page_number)] = feed_page


class FakeActivityLogRepository(ActivityLogRepositoryInterface):
    """An in-memory stand-in for `ActivityLogRepositoryInterface`."""

    def __init__(self, raise_on_record: Exception | None = None) -> None:
        self.recorded_events: list[ActivityEvent] = []
        self._raise_on_record = raise_on_record

    def record_activity_event(self, event: ActivityEvent) -> None:
        if self._raise_on_record is not None:
            raise self._raise_on_record
        self.recorded_events.append(event)
