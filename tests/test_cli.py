"""Tests for importer.cli."""

from __future__ import annotations

from pathlib import Path

import pytest
from pytest_mock import MockerFixture

from importer.cli import build_arg_parser, main


def test_arg_parser_defaults() -> None:
    args = build_arg_parser().parse_args(["users.csv"])
    assert args.csv_file == Path("users.csv")
    assert args.db == Path("db.json")
    assert args.verbose is False


def test_arg_parser_accepts_custom_db_and_verbose() -> None:
    args = build_arg_parser().parse_args(["users.csv", "--db", "custom.json", "-v"])
    assert args.db == Path("custom.json")
    assert args.verbose is True


def test_main_successful_import_returns_zero(
    valid_csv_path: Path, db_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    exit_code = main([str(valid_csv_path), "--db", str(db_path)])

    assert exit_code == 0
    captured = capsys.readouterr()
    assert "Imported:            3" in captured.out
    assert db_path.exists()


def test_main_with_errors_returns_one(
    mixed_csv_path: Path, db_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    exit_code = main([str(mixed_csv_path), "--db", str(db_path)])

    assert exit_code == 1
    captured = capsys.readouterr()
    assert "Rows with errors:    2" in captured.out


def test_main_missing_file_returns_one_and_prints_error(
    missing_csv_path: Path, db_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    exit_code = main([str(missing_csv_path), "--db", str(db_path)])

    assert exit_code == 1
    captured = capsys.readouterr()
    assert "Import failed" in captured.err


def test_main_verbose_flag_enables_debug_logging(
    valid_csv_path: Path, db_path: Path, mocker: MockerFixture
) -> None:
    configure_logging = mocker.patch("importer.cli.configure_logging")
    main([str(valid_csv_path), "--db", str(db_path), "-v"])
    configure_logging.assert_called_once_with(verbose=True)
