"""CSV parsing for the resilient data importer.

This module is only responsible for *reading* raw rows out of a CSV
file, as a context manager, so that the file handle is always closed
safely. It does not perform any data validation; that responsibility
belongs to :mod:`importer.validator` (single responsibility principle).
"""

from __future__ import annotations

import csv
import logging
from collections.abc import Iterator
from pathlib import Path
from types import TracebackType

from importer.exceptions import FileFormatError

logger = logging.getLogger(__name__)

#: Columns that must be present in the CSV header for a file to be importable.
REQUIRED_FIELDS: tuple[str, ...] = ("user_id", "name", "email")


class CsvUserReader:
    """Context manager that safely opens and reads a CSV file of users.

    Example:
        >>> with CsvUserReader("users.csv") as reader:
        ...     for row_number, raw_row in reader.rows():
        ...         print(row_number, raw_row)
    """

    def __init__(self, path: Path | str) -> None:
        """Initialize the reader.

        Args:
            path: Path to the CSV file to read.
        """
        self._path = Path(path)
        self._file: object | None = None
        self._reader: csv.DictReader[str] | None = None

    def __enter__(self) -> CsvUserReader:
        """Open the CSV file and validate its header row.

        Returns:
            This reader instance, ready to iterate via :meth:`rows`.

        Raises:
            FileFormatError: If the file is missing, unreadable, empty,
                or missing one of the :data:`REQUIRED_FIELDS`.
        """
        try:
            file_obj = self._path.open("r", newline="", encoding="utf-8")
        except FileNotFoundError as exc:
            raise FileFormatError(f"CSV file not found: {self._path}") from exc
        except OSError as exc:
            raise FileFormatError(f"Could not open CSV file {self._path}: {exc}") from exc

        self._file = file_obj
        reader = csv.DictReader(file_obj)

        if reader.fieldnames is None:
            self._close()
            raise FileFormatError(f"CSV file is empty: {self._path}")

        missing = [field for field in REQUIRED_FIELDS if field not in reader.fieldnames]
        if missing:
            self._close()
            raise FileFormatError(f"CSV file {self._path} is missing required column(s): {missing}")

        self._reader = reader
        logger.debug("Opened CSV file %s for reading", self._path)
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Close the underlying file handle, regardless of any error."""
        self._close()

    def _close(self) -> None:
        if self._file is not None:
            self._file.close()  # type: ignore[attr-defined]
            self._file = None

    def rows(self) -> Iterator[tuple[int, dict[str, str]]]:
        """Iterate over the data rows of the CSV file.

        Yields:
            Tuples of ``(row_number, raw_row)`` where ``row_number`` is a
            1-based index over data rows (the header is not counted) and
            ``raw_row`` is a mapping of column name to raw string value.

        Raises:
            RuntimeError: If called before entering the context manager.
        """
        if self._reader is None:
            raise RuntimeError("CsvUserReader.rows() called outside of 'with' block")
        yield from enumerate(self._reader, start=1)
