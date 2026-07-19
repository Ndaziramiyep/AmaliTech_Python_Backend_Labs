"""Tests for importer.logging_config."""

from __future__ import annotations

import logging

from importer.logging_config import configure_logging


def test_configure_logging_default_is_info_level() -> None:
    configure_logging(verbose=False)
    assert logging.getLogger().level == logging.INFO


def test_configure_logging_verbose_is_debug_level() -> None:
    configure_logging(verbose=True)
    assert logging.getLogger().level == logging.DEBUG
