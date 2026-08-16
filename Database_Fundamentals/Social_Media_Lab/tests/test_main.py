"""Unit tests for the `main.py` entry point: interactive menu vs. scriptable subcommand."""

from __future__ import annotations

import main as main_module
import pytest
from pytest_mock import MockerFixture


def test_main_launches_the_interactive_session_with_no_arguments(
    mocker: MockerFixture, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Running with no arguments at all launches the interactive menu-driven session."""
    monkeypatch.setattr("sys.argv", ["main.py"])
    fake_run_interactive_session = mocker.patch.object(
        main_module, "run_interactive_session", return_value=0
    )
    fake_run_command = mocker.patch.object(main_module, "run_command")

    exit_code = main_module.main()

    assert exit_code == 0
    fake_run_interactive_session.assert_called_once_with()
    fake_run_command.assert_not_called()


def test_main_dispatches_to_the_scriptable_command_parser_with_arguments(
    mocker: MockerFixture, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Any argument at all is handed off to the scriptable subcommand parser."""
    monkeypatch.setattr("sys.argv", ["main.py", "follow-user", "1", "2"])
    fake_run_command = mocker.patch.object(main_module, "run_command", return_value=0)
    fake_run_interactive_session = mocker.patch.object(main_module, "run_interactive_session")

    exit_code = main_module.main()

    assert exit_code == 0
    fake_run_command.assert_called_once_with()
    fake_run_interactive_session.assert_not_called()
