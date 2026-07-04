"""
logger.py
---------
Configures and exposes the application-wide logger for the Vehicle Rental System.

Logs are written to both the console (WARNING and above) and a rotating log file
(DEBUG and above) located at ``rental_system.log`` in the project root.
"""

import logging
from logging.handlers import RotatingFileHandler

_LOG_FILE = "rental_system.log"
_FMT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
_DATE_FMT = "%Y-%m-%d %H:%M:%S"


def get_logger(name: str) -> logging.Logger:
    """Return a named logger attached to the application's shared handlers.

    Args:
        name: Typically ``__name__`` of the calling module.

    Returns:
        A configured :class:`logging.Logger` instance.
    """
    logger = logging.getLogger(name)

    if not logger.handlers:
        logger.setLevel(logging.DEBUG)
        formatter = logging.Formatter(_FMT, datefmt=_DATE_FMT)

        # File handler — DEBUG and above, rotates at 1 MB, keeps 3 backups
        fh = RotatingFileHandler(_LOG_FILE, maxBytes=1_000_000, backupCount=3, encoding="utf-8")
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(formatter)

        # Console handler — WARNING and above
        ch = logging.StreamHandler()
        ch.setLevel(logging.WARNING)
        ch.setFormatter(formatter)

        logger.addHandler(fh)
        logger.addHandler(ch)

    return logger
