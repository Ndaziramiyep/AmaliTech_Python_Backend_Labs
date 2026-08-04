#!/usr/bin/env python
"""Thin entry point: create a post. See `social_platform.cli.create_post_command`."""

from __future__ import annotations

from social_platform.cli.create_post_command import main

if __name__ == "__main__":
    raise SystemExit(main())
