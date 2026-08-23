"""Application-specific exception hierarchy."""


class SocialError(Exception):
    """Base class for every error raised intentionally by this application."""


class UnitOfWorkStateError(SocialError, RuntimeError):
    """Raised when a UnitOfWork's cursor is read outside its `with` block."""
