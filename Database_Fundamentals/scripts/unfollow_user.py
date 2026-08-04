#!/usr/bin/env python
"""Thin entry point: unfollow a user. See `social_platform.cli.unfollow_user_command`."""

from __future__ import annotations

from social_platform.cli.unfollow_user_command import main

if __name__ == "__main__":
    raise SystemExit(main())
