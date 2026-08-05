#!/usr/bin/env python
"""Thin entry point: show trending posts. See `social_platform.cli.get_trending_posts_command`."""

from __future__ import annotations

from social_platform.cli.get_trending_posts_command import main

if __name__ == "__main__":
    raise SystemExit(main())
