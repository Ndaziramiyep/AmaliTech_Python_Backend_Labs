import logging

from src.logging_config import setup_logging


def test_setup_logging_execution():
    # Initialize logging
    setup_logging()

    # Create a logger and log messages at all levels
    logger = logging.getLogger("test_logger")
    logger.debug("debug message")
    logger.info("info message")
    logger.warning("warning message")
    logger.error("error message")
    logger.critical("critical message")

    # Check logger name to ensure logger was created
    assert logger.name == "test_logger"
