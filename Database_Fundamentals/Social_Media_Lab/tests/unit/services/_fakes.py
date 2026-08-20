"""Hand-written fakes of each feature's repository contract, for testing services without I/O.

Since every contract is a `typing.Protocol` (structural typing), these fakes don't need to
inherit from anything -- matching the shape is enough to satisfy the type checker.
"""

from __future__ import annotations

from datetime import datetime

from social_platform.common.exceptions import (
    CommentNotFoundError,
    PostNotFoundError,
    UserNotFoundError,
)
from social_platform.features.activity_log.model import ActivityEvent
from social_platform.features.comments.model import Comment, CommentThreadEntry
from social_platform.features.feed.model import FeedPostEntry
from social_platform.features.followers.model import FollowResult, UnfollowResult
from social_platform.features.likes.model import LikeResult, UnlikeResult
from social_platform.features.posts.model import Post, PostMetadata
from social_platform.features.trending.model import TrendingPostEntry
from social_platform.features.users.model import User


class FakeUserRepository:
    """An in-memory stand-in for `UserRepository`."""

    def __init__(self) -> None:
        self.users_by_id: dict[int, User] = {}
        self.password_hashes_by_username: dict[str, str] = {}
        self.next_user_id = 1

    def create_user(
        self, username: str, email: str, password_hash: str, bio: str | None = None
    ) -> User:
        user = User(self.next_user_id, username, email, bio, datetime.now())
        self.users_by_id[user.user_id] = user
        self.password_hashes_by_username[username] = password_hash
        self.next_user_id += 1
        return user

    def find_user_and_password_hash_by_username(self, username: str) -> tuple[User, str] | None:
        password_hash = self.password_hashes_by_username.get(username)
        if password_hash is None:
            return None
        user = next(user for user in self.users_by_id.values() if user.username == username)
        return user, password_hash

    def find_user_by_username(self, username: str) -> User | None:
        return next((user for user in self.users_by_id.values() if user.username == username), None)

    def update_bio(self, user_id: int, bio: str | None) -> User:
        user = self.users_by_id.get(user_id)
        if user is None:
            raise UserNotFoundError(f"No user with id {user_id!r} exists.")
        updated_user = User(user.user_id, user.username, user.email, bio, user.created_at)
        self.users_by_id[user_id] = updated_user
        return updated_user

    def search_users_by_username(self, query: str, result_limit: int) -> list[User]:
        matches = [
            user for user in self.users_by_id.values() if query.lower() in user.username.lower()
        ]
        return sorted(matches, key=lambda user: user.username)[:result_limit]


class FakePostRepository:
    """An in-memory stand-in for `PostRepository`."""

    def __init__(self) -> None:
        self.posts_by_id: dict[int, Post] = {}
        self.next_post_id = 1

    def create_post(self, author_user_id: int, content: str, metadata: PostMetadata) -> Post:
        post = Post(self.next_post_id, author_user_id, content, metadata, datetime.now())
        self.posts_by_id[post.post_id] = post
        self.next_post_id += 1
        return post

    def find_post_by_id(self, post_id: int) -> Post | None:
        return self.posts_by_id.get(post_id)

    def find_posts_by_author(self, author_user_id: int, result_limit: int) -> list[Post]:
        own_posts = [
            post for post in self.posts_by_id.values() if post.author_user_id == author_user_id
        ]
        return sorted(own_posts, key=lambda post: post.post_id, reverse=True)[:result_limit]

    def update_post(
        self, post_id: int, author_user_id: int, content: str, metadata: PostMetadata
    ) -> Post:
        post = self.posts_by_id.get(post_id)
        if post is None or post.author_user_id != author_user_id:
            raise PostNotFoundError(f"No post with id {post_id!r} owned by {author_user_id!r}.")
        updated_post = Post(post_id, author_user_id, content, metadata, post.created_at)
        self.posts_by_id[post_id] = updated_post
        return updated_post

    def delete_post(self, post_id: int, author_user_id: int) -> None:
        post = self.posts_by_id.get(post_id)
        if post is None or post.author_user_id != author_user_id:
            raise PostNotFoundError(f"No post with id {post_id!r} owned by {author_user_id!r}.")
        del self.posts_by_id[post_id]

    def count_posts_by_author(self, author_user_id: int) -> int:
        return sum(1 for post in self.posts_by_id.values() if post.author_user_id == author_user_id)


class FakeCommentRepository:
    """An in-memory stand-in for `CommentRepository`."""

    def __init__(self) -> None:
        self.comments_by_id: dict[int, Comment] = {}
        self.next_comment_id = 1

    def create_comment(
        self,
        post_id: int,
        commenter_user_id: int,
        content: str,
        parent_comment_id: int | None = None,
    ) -> Comment:
        comment = Comment(
            self.next_comment_id,
            post_id,
            commenter_user_id,
            parent_comment_id,
            content,
            datetime.now(),
        )
        self.comments_by_id[comment.comment_id] = comment
        self.next_comment_id += 1
        return comment

    def find_comment_by_id(self, comment_id: int) -> Comment | None:
        return self.comments_by_id.get(comment_id)

    def find_comment_thread_for_post(self, post_id: int) -> list[CommentThreadEntry]:
        comments = [
            comment for comment in self.comments_by_id.values() if comment.post_id == post_id
        ]
        children_by_parent: dict[int | None, list[Comment]] = {}
        for comment in sorted(comments, key=lambda comment: comment.comment_id):
            children_by_parent.setdefault(comment.parent_comment_id, []).append(comment)

        entries: list[CommentThreadEntry] = []

        def visit(parent_comment_id: int | None, depth: int) -> None:
            for comment in children_by_parent.get(parent_comment_id, []):
                entries.append(CommentThreadEntry(comment=comment, depth=depth))
                visit(comment.comment_id, depth + 1)

        visit(None, 0)
        return entries

    def delete_comment(self, comment_id: int, commenter_user_id: int) -> None:
        comment = self.comments_by_id.get(comment_id)
        if comment is None or comment.commenter_user_id != commenter_user_id:
            raise CommentNotFoundError(
                f"No comment with id {comment_id!r} owned by {commenter_user_id!r}."
            )
        del self.comments_by_id[comment_id]


class FakeTagRepository:
    """An in-memory stand-in for `TagRepository`."""

    def __init__(self) -> None:
        self.tags_by_post_id: dict[int, list[str]] = {}

    def attach_tags(self, post_id: int, tag_names: list[str]) -> None:
        existing = self.tags_by_post_id.setdefault(post_id, [])
        for tag_name in tag_names:
            if tag_name not in existing:
                existing.append(tag_name)

    def get_tags_for_post(self, post_id: int) -> list[str]:
        return sorted(self.tags_by_post_id.get(post_id, []))


class FakeFollowerRepository:
    """An in-memory stand-in for `FollowerRepository`."""

    def __init__(self) -> None:
        self.follow_result_to_return = FollowResult.CREATED
        self.unfollow_result_to_return = UnfollowResult.REMOVED
        self.create_calls: list[tuple[int, int]] = []
        self.delete_calls: list[tuple[int, int]] = []
        self.follower_count_to_return = 0
        self.following_count_to_return = 0
        self.is_following_to_return = False

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

    def count_followers(self, user_id: int) -> int:
        return self.follower_count_to_return

    def count_following(self, user_id: int) -> int:
        return self.following_count_to_return

    def is_following(self, follower_user_id: int, followee_user_id: int) -> bool:
        return self.is_following_to_return


class FakeLikeRepository:
    """An in-memory stand-in for `LikeRepository`."""

    def __init__(self) -> None:
        self.like_result_to_return = LikeResult.CREATED
        self.unlike_result_to_return = UnlikeResult.REMOVED
        self.create_calls: list[tuple[int, int]] = []
        self.delete_calls: list[tuple[int, int]] = []
        self.has_liked_to_return = False

    def create_like(self, post_id: int, user_id: int) -> LikeResult:
        self.create_calls.append((post_id, user_id))
        return self.like_result_to_return

    def delete_like(self, post_id: int, user_id: int) -> UnlikeResult:
        self.delete_calls.append((post_id, user_id))
        return self.unlike_result_to_return

    def has_user_liked(self, post_id: int, user_id: int) -> bool:
        return self.has_liked_to_return


class FakeFeedRepository:
    """An in-memory stand-in for `FeedRepository`."""

    def __init__(self) -> None:
        self.feed_page_calls: list[tuple[int, int, int]] = []
        self.feed_page_to_return: list[FeedPostEntry] = []

    def fetch_feed_page(
        self, follower_user_id: int, first_row: int, last_row: int
    ) -> list[FeedPostEntry]:
        self.feed_page_calls.append((follower_user_id, first_row, last_row))
        return self.feed_page_to_return


class FakeTrendingRepository:
    """An in-memory stand-in for `TrendingRepository`."""

    def __init__(self) -> None:
        self.trending_posts_to_return: list[TrendingPostEntry] = []

    def fetch_trending_posts(self, since: datetime, result_limit: int) -> list[TrendingPostEntry]:
        return self.trending_posts_to_return


class FakeTimelineCache:
    """An in-memory stand-in for `TimelineCache`."""

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


class FakeActivityLogRepository:
    """An in-memory stand-in for `ActivityLogRepository`."""

    def __init__(self, raise_on_record: Exception | None = None) -> None:
        self.recorded_events: list[ActivityEvent] = []
        self._raise_on_record = raise_on_record

    def record_activity_event(self, event: ActivityEvent) -> None:
        if self._raise_on_record is not None:
            raise self._raise_on_record
        self.recorded_events.append(event)
