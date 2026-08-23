"""Application-specific exceptions, re-exported for
`from social.exceptions import X`.
"""
from social.exceptions.errors import SocialError, UnitOfWorkStateError

__all__ = ["SocialError", "UnitOfWorkStateError"]
