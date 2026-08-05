#!/usr/bin/env python
"""Thin entry point: like a post. See `social_platform.cli.like_post_command`."""

from __future__ import annotations

from social_platform.cli.like_post_command import main

if __name__ == "__main__":
    raise SystemExit(main())
