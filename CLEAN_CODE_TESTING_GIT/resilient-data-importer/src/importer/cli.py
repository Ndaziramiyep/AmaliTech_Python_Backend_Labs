"""Command-line entry point for the resilient data importer.

Usage:
    resilient-importer path/to/users.csv --db path/to/db.json
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from importer.exceptions import ImporterError
from importer.logging_config import configure_logging
from importer.service import ImportService

logger = logging.getLogger(__name__)


def build_arg_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser.

    Returns:
        A configured :class:`argparse.ArgumentParser`.
    """
    parser = argparse.ArgumentParser(
        prog="resilient-importer",
        description="Import user data from a CSV file into a JSON-backed database.",
    )
    parser.add_argument("csv_file", type=Path, help="Path to the source CSV file.")
    parser.add_argument(
        "--db",
        type=Path,
        default=Path("db.json"),
        help="Path to the JSON database file (default: %(default)s).",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable debug-level logging.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the importer CLI.

    Args:
        argv: Command-line arguments, excluding the program name. Defaults
            to ``sys.argv[1:]`` when ``None``.

    Returns:
        Process exit code: ``0`` on a fully clean import, ``1`` if any
        row failed validation or the import could not proceed at all.
    """
    args = build_arg_parser().parse_args(argv)
    configure_logging(verbose=args.verbose)

    service = ImportService()
    try:
        summary = service.import_csv(args.csv_file, args.db)
    except ImporterError as exc:
        logger.error("Import aborted: %s", exc)
        print(f"Import failed: {exc}", file=sys.stderr)
        return 1

    print(f"Imported:            {summary.imported}")
    print(f"Duplicates skipped:  {len(summary.duplicates)}")
    print(f"Rows with errors:    {len(summary.errors)}")

    return 1 if summary.has_errors else 0


if __name__ == "__main__":
    sys.exit(main())
