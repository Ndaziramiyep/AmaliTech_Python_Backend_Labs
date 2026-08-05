#!/usr/bin/env python
"""Thin entry point: add a comment. See `social_platform.cli.add_comment_command`."""

from __future__ import annotations

from social_platform.cli.add_comment_command import main

if __name__ == "__main__":
    raise SystemExit(main())
