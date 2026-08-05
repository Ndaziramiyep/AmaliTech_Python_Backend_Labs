"""Composition root for the register-user CLI command."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence

from social_platform.cli._composition import build_repository_bundle
from social_platform.models.exceptions import SocialPlatformError
from social_platform.services.user_registration_service import UserRegistrationService


def main(argv: Sequence[str] | None = None) -> int:
    """Parse arguments and register a new user."""
    parser = argparse.ArgumentParser(description="Register a new user.")
    parser.add_argument("username")
    parser.add_argument("email")
    parser.add_argument("password")
    parser.add_argument("display_name")
    parsed_arguments = parser.parse_args(argv)

    repository_bundle = build_repository_bundle()
    registration_service = UserRegistrationService(repository_bundle.user_repository)
    try:
        user = registration_service.register_user(
            parsed_arguments.username,
            parsed_arguments.email,
            parsed_arguments.password,
            parsed_arguments.display_name,
        )
    except SocialPlatformError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    finally:
        repository_bundle.connection_pool.close_all_connections()

    print(f"Registered user {user.user_id} (@{user.username}).")
    return 0
