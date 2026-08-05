#!/usr/bin/env python
"""Thin entry point: register a user. See `social_platform.cli.register_user_command`."""

from __future__ import annotations

from social_platform.cli.register_user_command import main

if __name__ == "__main__":
    raise SystemExit(main())
