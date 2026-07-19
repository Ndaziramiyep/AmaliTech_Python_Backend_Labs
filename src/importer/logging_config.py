"""Structured logging configuration for the importer CLI."""

from __future__ import annotations

import logging

_LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def configure_logging(verbose: bool = False) -> None:
    """Configure root logging handlers and message format.

    Args:
        verbose: If ``True``, set the root logger level to ``DEBUG``;
            otherwise use ``INFO``.
    """
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format=_LOG_FORMAT, datefmt=_DATE_FORMAT, force=True)
