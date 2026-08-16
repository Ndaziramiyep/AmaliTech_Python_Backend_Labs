#!/usr/bin/env python
"""Entry point: the interactive menu with no arguments, or a scriptable subcommand."""

from __future__ import annotations

import sys

from social_platform.cli.commands import main as run_command
from social_platform.cli.interactive import run_interactive_session


def main() -> int:
    """Launch the interactive menu with no arguments, otherwise dispatch to a subcommand."""
    if len(sys.argv) == 1:
        return run_interactive_session()
    return run_command()


if __name__ == "__main__":
    raise SystemExit(main())
