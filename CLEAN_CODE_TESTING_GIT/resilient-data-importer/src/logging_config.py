import logging
from pathlib import Path


def setup_logging() -> None:
    logger = logging.getLogger()

    if logger.handlers:
        return  # Prevent duplicate handlers in pytest

    logger.setLevel(logging.INFO)

    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)

    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")

    console = logging.StreamHandler()
    console.setFormatter(formatter)

    file_handler = logging.FileHandler(logs_dir / "importer.log")
    file_handler.setFormatter(formatter)

    logger.addHandler(console)
    logger.addHandler(file_handler)
