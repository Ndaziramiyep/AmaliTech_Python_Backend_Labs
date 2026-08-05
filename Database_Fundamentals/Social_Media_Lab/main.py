#!/usr/bin/env python
"""Unified CLI entry point: dispatches to each composition-root command in `social_platform.cli`."""

from __future__ import annotations

import sys
from collections.abc import Callable, Sequence

from social_platform.cli.add_comment_command import main as add_comment_main
from social_platform.cli.create_post_command import main as create_post_main
from social_platform.cli.follow_user_command import main as follow_user_main
from social_platform.cli.get_trending_posts_command import main as get_trending_posts_main
from social_platform.cli.get_user_feed_command import main as get_user_feed_main
from social_platform.cli.interactive_session import run_interactive_session
from social_platform.cli.like_post_command import main as like_post_main
from social_platform.cli.register_user_command import main as register_user_main
from social_platform.cli.unfollow_user_command import main as unfollow_user_main

_COMMANDS: dict[str, Callable[[Sequence[str]], int]] = {
    "register-user": register_user_main,
    "create-post": create_post_main,
    "follow-user": follow_user_main,
    "unfollow-user": unfollow_user_main,
    "add-comment": add_comment_main,
    "like-post": like_post_main,
    "get-user-feed": get_user_feed_main,
    "get-trending-posts": get_trending_posts_main,
}


def main(argv: Sequence[str] | None = None) -> int:
    """Dispatch to the requested subcommand's composition-root `main`, or print usage.

    With no arguments at all, launches the interactive menu-driven session instead.
    """
    arguments = list(argv if argv is not None else sys.argv[1:])
    if not arguments:
        return run_interactive_session()
    if arguments[0] not in _COMMANDS:
        _print_usage()
        return 0 if arguments[:1] in (["-h"], ["--help"]) else 1

    command_name, *command_arguments = arguments
    return _COMMANDS[command_name](command_arguments)


def _print_usage() -> None:
    print("Usage: python main.py <command> [arguments...]")
    print("\nCommands:")
    for command_name in _COMMANDS:
        print(f"  {command_name}")
    print("\nEach command also accepts -h/--help for its own arguments.")


if __name__ == "__main__":
    raise SystemExit(main())
