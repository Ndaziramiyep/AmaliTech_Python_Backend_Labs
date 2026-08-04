#!/usr/bin/env python
"""Thin entry point: show a user's feed. See `social_platform.cli.get_user_feed_command`."""

from __future__ import annotations

from social_platform.cli.get_user_feed_command import main

if __name__ == "__main__":
    raise SystemExit(main())
