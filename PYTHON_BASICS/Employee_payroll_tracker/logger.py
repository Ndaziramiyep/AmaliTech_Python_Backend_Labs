"""
logger.py
Centralised logging configuration for the Employee Payroll Tracker.

All modules import `get_logger(__name__)` to obtain a named logger that
writes to both the console (WARNING+) and a rotating log file (DEBUG+).

Log file: logs/payroll.log
    - Rotates at 1 MB, keeps 3 backups.
    - Each line includes timestamp, level, module name, and message.
"""

import logging
import os
from logging.handlers import RotatingFileHandler

# Always resolve logs/ relative to this file's directory (project root)
_LOG_DIR  = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
_LOG_FILE = os.path.join(_LOG_DIR, "payroll.log")
_FMT      = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
_DATE_FMT = "%Y-%m-%d %H:%M:%S"


def _build_root_logger() -> None:
    """Configure the root logger once when this module is first imported."""
    root = logging.getLogger()
    if root.handlers:
        return  # already configured — avoid duplicate handlers

    root.setLevel(logging.DEBUG)

    # File handler — DEBUG and above, rotating at 1 MB, 3 backups
    os.makedirs(_LOG_DIR, exist_ok=True)
    file_handler = RotatingFileHandler(
        _LOG_FILE, maxBytes=1_000_000, backupCount=3, encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(_FMT, datefmt=_DATE_FMT))

    # Console handler — WARNING and above (keeps CLI output clean)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)
    console_handler.setFormatter(logging.Formatter(_FMT, datefmt=_DATE_FMT))

    root.addHandler(file_handler)
    root.addHandler(console_handler)


_build_root_logger()


def get_logger(name: str) -> logging.Logger:
    """
    Return a named logger for the given module.

    Args:
        name: Typically __name__ of the calling module.

    Returns:
        A configured logging.Logger instance.
    """
    return logging.getLogger(name)
