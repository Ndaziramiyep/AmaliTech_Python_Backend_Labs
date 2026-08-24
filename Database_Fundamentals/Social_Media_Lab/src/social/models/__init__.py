"""Pure dataclasses describing the domain, with no I/O or driver imports."""
from social.models.comment import Comment
from social.models.follower import Follower
from social.models.like import Like
from social.models.post import Post
from social.models.user import User

__all__ = ["Comment", "Follower", "Like", "Post", "User"]
