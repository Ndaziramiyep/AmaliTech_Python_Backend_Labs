"""Unit tests for the domain exception hierarchy."""

from __future__ import annotations

import pytest

from social_platform.models.exceptions import (
    ConnectionPoolExhaustedError,
    InvalidFollowOperationError,
    PostNotFoundError,
    SocialPlatformError,
    UserNotFoundError,
)


@pytest.mark.parametrize(
    "exception_class",
    [
        UserNotFoundError,
        PostNotFoundError,
        InvalidFollowOperationError,
        ConnectionPoolExhaustedError,
    ],
)
def test_every_domain_exception_is_a_social_platform_error(
    exception_class: type[SocialPlatformError],
) -> None:
    """Every domain exception can be caught generically via SocialPlatformError."""
    assert issubclass(exception_class, SocialPlatformError)
